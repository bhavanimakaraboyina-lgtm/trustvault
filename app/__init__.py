
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from app.extensions import db, login_manager, csrf, limiter


def create_app(test_config=None):

    project_folder = Path(__file__).resolve().parent.parent
    load_dotenv(project_folder / ".env")

    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    database_path = Path(app.instance_path) / "trustvault.db"

    secret_key = os.getenv("SECRET_KEY")
    is_production = os.getenv("FLASK_ENV", "").lower() == "production"

    if (
        is_production
        and not secret_key
        and not (test_config and test_config.get("SECRET_KEY"))
    ):
        raise RuntimeError(
            "SECRET_KEY must be configured in production."
        )

    app.config["SECRET_KEY"] = secret_key or "development-only-key"

    # Use PostgreSQL when DATABASE_URL is provided.
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://",
                "postgresql+psycopg://",
                1
            )
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1
            )

        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        # Use SQLite for local development.
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "sqlite:///" + database_path.as_posix()
        )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True
    }

    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = is_production

    # Allow test configuration to override default settings.
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"

    # Register application routes.
    from app.routes.auth import auth
    from app.routes.documents import documents

    app.register_blueprint(auth)
    app.register_blueprint(documents)

    # Load database models and create database tables.
    from app import models

    with app.app_context():
        db.create_all()

    return app
