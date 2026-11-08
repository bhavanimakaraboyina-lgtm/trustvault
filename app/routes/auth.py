
import re

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models import User

auth = Blueprint("auth", __name__)


def is_valid_gmail(email):
    return bool(re.fullmatch(
        r"[A-Za-z0-9._%+-]+@gmail\.com",
        email.strip()
    ))


def is_strong_password(password):
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"\d", password)
        and re.search(r"[^A-Za-z0-9]", password)
    )


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("documents.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("auth.register"))

        if not is_valid_gmail(email):
            flash("Please use a valid Gmail address.", "error")
            return redirect(url_for("auth.register"))

        if not is_strong_password(password):
            flash(
                "Password must contain at least 8 characters, "
                "one uppercase letter, one lowercase letter, "
                "one number and one special character.",
                "error"
            )
            return redirect(url_for("auth.register"))

        existing_user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if existing_user:
            flash("An account with this email already exists.", "error")
            return redirect(url_for("auth.register"))

        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="viewer"
        )

        db.session.add(new_user)
        db.session.commit()

        flash(
            "Registration successful. You can now sign in as a Viewer.",
            "success"
        )
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("documents.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        selected_role = request.form.get("login_role", "").strip().lower()

        if selected_role not in ("admin", "owner", "viewer"):
            flash("Please select a valid login type.", "error")
            return redirect(url_for("auth.login"))

        user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if (
            not user
            or not check_password_hash(user.password_hash, password)
        ):
            flash("Invalid email or password.", "error")
            return redirect(url_for("auth.login"))

        # Selecting a role does not grant that role.
        # The selected role must match the role stored in the database.
        if user.role != selected_role:
            flash(
                "This account does not belong to the selected login type.",
                "error"
            )
            return redirect(url_for("auth.login"))

        login_user(user)

        if user.must_change_password:
            flash("Please change your temporary password.", "warning")
            return redirect(url_for("auth.change_password"))

        flash("Login successful.", "success")
        return redirect(url_for("documents.dashboard"))

    return render_template("login.html")


@auth.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not check_password_hash(
            current_user.password_hash, current_password
        ):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("auth.change_password"))

        if not is_strong_password(new_password):
            flash(
                "New password must contain at least 8 characters, "
                "one uppercase letter, one lowercase letter, "
                "one number and one special character.",
                "error"
            )
            return redirect(url_for("auth.change_password"))

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return redirect(url_for("auth.change_password"))

        current_user.password_hash = generate_password_hash(new_password)
        current_user.must_change_password = False
        db.session.commit()

        flash("Password changed successfully.", "success")
        return redirect(url_for("documents.dashboard"))

    return render_template("change_password.html")


@auth.route("/forgot-password", methods=["GET"])
def forgot_password():
    return render_template("forgot_password.html")


@auth.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
