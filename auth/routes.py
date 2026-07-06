from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from authlib.common.security import generate_token
from authlib.integrations.base_client import OAuthError

from bson import ObjectId
from flask import current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash, generate_password_hash

from auth import auth_bp
from database.db import get_db
from extensions import loginManager, oauth
from forms.forms import LoginForm, SignupForm
from model.user import User


def _safe_next(target):
    host = urlparse(request.host_url)
    candidate = urlparse(urljoin(request.host_url, target or ""))
    return candidate.scheme in {"http", "https"} and candidate.netloc == host.netloc


@loginManager.user_loader
def load_user(user_id):
    try:
        data = get_db().users.find_one({"_id": ObjectId(user_id)})
    except (ValueError, TypeError):
        return None
    return User(data) if data else None


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data.strip().lower()
        email = form.email.data.strip().lower()
        try:
            result = get_db().users.insert_one({
                "username": username,
                "email": email,
                "password": generate_password_hash(form.password.data, method="scrypt"),
                "provider": "local",
                "provider_id": f"local:{username}",
                "profile_pic": "",
                "bio": "",
                "role": "reader",
                "created_at": datetime.now(timezone.utc),
            })
        except DuplicateKeyError:
            flash("That username or email is already registered.", "danger")
        else:
            login_user(User(get_db().users.find_one({"_id": result.inserted_id})))
            flash("Welcome to ShazBlog — your account is ready.", "success")
            return redirect(url_for("profile"))
    return render_template("auth.html", form=form, mode="signup")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))
    form = LoginForm()
    if form.validate_on_submit():
        identity = form.identity.data.strip().lower()
        data = get_db().users.find_one({"$or": [{"username": identity}, {"email": identity}], "provider": "local"})
        if data and data.get("password") and check_password_hash(data["password"], form.password.data):
            login_user(User(data), remember=form.remember.data)
            destination = request.args.get("next")
            return redirect(destination if _safe_next(destination) else url_for("profile"))
        flash("We couldn't match those credentials. Please try again.", "danger")
    providers = [name for name in ("google", "github", "linkedin", "facebook") if current_app.config.get(f"{name.upper()}_CLIENT_ID")]
    return render_template("auth.html", form=form, mode="login", providers=providers)


@auth_bp.post("/logout")
def logout():
    logout_user()
    flash("You've been signed out safely.", "info")
    return redirect(url_for("index"))


OIDC_PROVIDERS = {"google", "linkedin"}
def _fetch_token_no_id_verification(client):
    """LinkedIn's OIDC id_token frequently omits the 'nonce' claim even when
    one was requested, which makes Authlib's built-in ID-token verification
    raise MissingClaimError. We don't need ID-token verification here since
    we fetch the profile from the userinfo REST endpoint directly, so fetch
    the access token without triggering that automatic check."""
    if request.method == "GET":
        error = request.args.get("error")
        if error:
            raise OAuthError(error=error, description=request.args.get("error_description"))
        params = {"code": request.args.get("code"), "state": request.args.get("state")}
    else:
        params = {"code": request.form.get("code"), "state": request.form.get("state")}
    state_data = client.framework.get_state_data(session, params.get("state"))
    client.framework.clear_state_data(session, params.get("state"))
    params = client._format_state_params(state_data, params)
    token = client.fetch_access_token(**params)
    client.token = token
    return token
def _oauth_start(provider):
    if not current_app.config.get(f"{provider.upper()}_CLIENT_ID"):
        flash(f"{provider.title()} sign-in is not configured.", "warning")
        return redirect(url_for("auth.login"))
    client = oauth.create_client(provider)
    redirect_uri = url_for(f"auth.{provider}_callback", _external=True)
    if provider in OIDC_PROVIDERS:
        nonce = generate_token()
        session[f"{provider}_nonce"] = nonce  # optional bookkeeping; Authlib manages its own copy internally
        return client.authorize_redirect(redirect_uri, nonce=nonce)
    return client.authorize_redirect(redirect_uri)


def _oauth_finish(provider, userinfo_url=None):
    client = oauth.create_client(provider)
    try:
        if provider == "linkedin":
            token = _fetch_token_no_id_verification(client)
        else:
            token = client.authorize_access_token()
        info = token.get("userinfo") or client.get(userinfo_url).json()
        provider_id = str(info.get("sub") or info.get("id"))
        if not provider_id or provider_id == "None":
            raise ValueError("No provider user ID returned")
    except Exception:
        current_app.logger.exception("OAuth callback failed for %s", provider)
        flash("Social sign-in could not be completed. Please try another method.", "danger")
        return redirect(url_for("auth.login"))
    database = get_db()
    email = (info.get("email") or "").lower()
    identities = [{"provider": provider, "provider_id": provider_id}]
    if email:
        identities.append({"email": email})
    data = database.users.find_one({"$or": identities})
    if not data:
        base = (info.get("preferred_username") or info.get("name") or f"{provider}-reader").strip().lower().replace(" ", "-")[:24]
        username = base
        suffix = 1
        while database.users.find_one({"username": username}):
            suffix += 1
            username = f"{base[:20]}-{suffix}"
        avatar = info.get("picture") or info.get("avatar_url") or ""
        if isinstance(avatar, dict):
            avatar = avatar.get("data", {}).get("url", "")
        result = database.users.insert_one({"provider": provider, "provider_id": provider_id, "username": username,
            "email": email, "profile_pic": avatar, "bio": "", "role": "reader",
            "created_at": datetime.now(timezone.utc)})
        data = database.users.find_one({"_id": result.inserted_id})
    login_user(User(data))
    return redirect(url_for("profile"))


@auth_bp.get("/login/google")
def google_auth(): return _oauth_start("google")
@auth_bp.get("/auth/google/callback")
def google_callback(): return _oauth_finish("google", "https://openidconnect.googleapis.com/v1/userinfo")
@auth_bp.get("/login/github")
def github_auth(): return _oauth_start("github")
@auth_bp.get("/auth/github/callback")
def github_callback(): return _oauth_finish("github", "https://api.github.com/user")
@auth_bp.get("/login/linkedin")
def linkedin_auth(): return _oauth_start("linkedin")
@auth_bp.get("/auth/linkedin/callback")
def linkedin_callback(): return _oauth_finish("linkedin", "https://api.linkedin.com/v2/userinfo")
@auth_bp.get("/login/facebook")
def facebook_auth(): return _oauth_start("facebook")
@auth_bp.get("/auth/facebook/callback")
def facebook_callback(): return _oauth_finish("facebook", "me?fields=id,name,email,picture")
