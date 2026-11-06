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

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY", "development-key-change-before-deployment"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + database_path.as_posix()
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if test_config:
        app.config.update(test_config)
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = (
        os.getenv("FLASK_ENV") == "production"
    )

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"

    # Register application routes
    from app.routes.auth import auth
    from app.routes.documents import documents

    app.register_blueprint(auth)
    app.register_blueprint(documents)

    # Load database models
    from app import models
    with app.app_context():
        db.create_all()
    return app