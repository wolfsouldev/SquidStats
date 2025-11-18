from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, UserMixin
from database.database import get_session, AuthUser
from urllib.parse import urlparse
from config import logger


auth_bp = Blueprint("auth", __name__)


class DBUser(UserMixin):
    def __init__(self, id_, username, role_id=None):
        self.id = str(id_)
        self.username = username
        self.role_id = role_id

    def get_role(self):
        return self.role_id


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        session = get_session()
        try:
            user = session.query(AuthUser).filter(AuthUser.username == username).first()
            if user and user.check_password(password):
                # Verificar si el usuario está activo
                if user.is_active == 0:
                    flash(
                        "Esta cuenta ha sido desactivada. Contacta al administrador para más información.",
                        "warning",
                    )
                    logger.warning(
                        f"Attempted login with deactivated account: {user.username}"
                    )
                else:
                    user_obj = DBUser(user.id, user.username, role_id=user.role_id)
                    login_user(user_obj)
                    logger.debug(
                        f"User logged in: id={user.id} username={user.username}"
                    )

                    # Safe redirect: only allow relative/internal paths
                    next_url = request.args.get("next") or request.form.get("next")
                    if next_url:
                        parsed = urlparse(next_url)
                        if parsed.netloc == "" and parsed.scheme == "":
                            return redirect(next_url)

                    return redirect(url_for("main.index"))
            else:
                flash("Usuario o contraseña inválidos", "danger")
        finally:
            session.close()

    return render_template("login.html", page_title="Login")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
