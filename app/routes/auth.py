
import re

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)
from werkzeug.security import (
    generate_password_hash, check_password_hash
)

from app.extensions import db
from app.models import User

auth = Blueprint("auth", __name__)


# Password change enforcement
@auth.before_app_request
def enforce_password_change():
    if (
        current_user.is_authenticated
        and current_user.must_change_password
        and request.endpoint not in (
            "auth.change_password",
            "auth.logout",
            "static"
        )
    ):
        return redirect(url_for("auth.change_password"))


# Gmail validation
def is_valid_gmail(email):
    return bool(
        re.fullmatch(r"[A-Za-z0-9._%+-]+@gmail\.com", email)
    )


# Strong password validation
def is_strong_password(password):
    return (
        len(password) >= 8
        and any(c.isupper() for c in password)
        and any(c.islower() for c in password)
        and any(c.isdigit() for c in password)
        and any(not c.isalnum() and not c.isspace() for c in password)
    )


# Registration
@auth.route("/register", methods=["GET", "POST"])
def register():

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
                "Password needs 8 characters, uppercase, lowercase, "
                "number and special symbol.",
                "error"
            )
            return redirect(url_for("auth.register"))

        existing_user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if existing_user:
            flash("This email is already registered.", "error")
            return redirect(url_for("auth.register"))

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="owner"
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# Login
@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if user and check_password_hash(user.password_hash, password):

            login_user(user)

            if user.must_change_password:
                flash("Please change your temporary password.", "error")
                return redirect(url_for("auth.change_password"))

            return redirect(url_for("documents.dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# Change Password
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
                "New password needs 8 characters, uppercase, lowercase, "
                "number and special symbol.",
                "error"
            )
            return redirect(url_for("auth.change_password"))

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return redirect(url_for("auth.change_password"))

        if new_password == current_password:
            flash("Choose a different password.", "error")
            return redirect(url_for("auth.change_password"))

        current_user.password_hash = generate_password_hash(new_password)
        current_user.must_change_password = False

        db.session.commit()

        flash("Password changed successfully.", "success")
        return redirect(url_for("documents.dashboard"))

    return render_template("change_password.html")


# Forgot Password
@auth.route("/forgot-password")
def forgot_password():
    return render_template("forgot_password.html")


# Logout
@auth.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    flash("You have been logged out.", "success")

    return redirect(url_for("auth.login"))
