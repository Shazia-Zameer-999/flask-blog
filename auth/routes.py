from flask import render_template, redirect, url_for,request
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user, logout_user
from model.user import User
from forms.forms import LoginForm, SignupForm
from database.db import db
from auth import auth_bp
from extensions import oauth,loginManager
from bson import ObjectId
import requests
from flask import current_app as app



@loginManager.user_loader
def load_user(user_id):
    if user_id:
        user_data = db.users.find_one({"_id": ObjectId(user_id)})
        return User(user_data) if user_data else None
    else:
        print("user_id not found")
@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data.lower()
        password = form.password.data
        hashed_password = generate_password_hash(
            password, method="scrypt", salt_length=16
        )
        existing_user = db.users.find_one({"username": username})
        if existing_user:
            return redirect(url_for("auth.signup"))
        signup_data = db.users.insert_one(
            {
                "username": username,
                "password": hashed_password,
                "provider": "local",
                "provider_id": "none",
                "email": "none",
                "profile_pic": "none",
            }
        )
        return redirect(url_for("auth.login"))
    return render_template("signup.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user_data = db.users.find_one({"username": username})
        if user_data and check_password_hash(user_data["password"], password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for("index"))
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth_bp.route("/login/google", methods=["GET", "POST"])
def google_auth():
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route("/auth/google/callback")
def google_callback():
    code = request.args.get("code")
    token = oauth.google.authorize_access_token()
    response = oauth.google.get("https://openidconnect.googleapis.com/v1/userinfo")
    user_info = response.json()
    user_data = db.users.find_one(
        {"provider": "google", "provider_id": user_info.get("sub")}
    )
    if not user_data:
        stored_user = db.users.insert_one(
            {
                "provider": "google",
                "provider_id": user_info.get("sub"),
                "username": user_info.get("name"),
                "email": user_info.get("email"),
                "profile_pic": user_info.get("picture"),
            }
        )
        user_data = db.users.find_one({"username": user_info["name"]})

    user = User(user_data)
    login_user(user)
    return redirect(url_for("index"))
@auth_bp.route("/login/linkedin", methods=["GET", "POST"])
def linkedin_auth():
    redirect_uri = url_for("auth.linkedin_callback", _external=True)
    return oauth.linkedin.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/linkedin/callback")
def linkedin_callback():
    code = request.args.get("code")
    redirect_uri = url_for("auth.linkedin_callback", _external=True)
    token_response = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": app.config["LINKEDIN_CLIENT_ID"],
            "client_secret": app.config["LINKEDIN_CLIENT_SECRET"],
        },
    )
    token_data = token_response.json()
    access_token = token_data["access_token"]
    user_response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    user_info = user_response.json()
    user_data = db.users.find_one(
        {"provider": "linkedin", "provider_id": user_info.get("sub")}
    )
    if not user_data:
        stored_user = db.users.insert_one(
            {
                "provider": "linkedin",
                "provider_id": user_info.get("sub"),
                "username": user_info.get("name"),
                "email": user_info.get("email"),
                "profile_pic": user_info.get("picture"),
            }
        )
        user_data = db.users.find_one({"username": user_info["name"]})

    user = User(user_data)
    login_user(user)
    return redirect(url_for("index"))


@auth_bp.route("/login/github")
def github_auth():
    redirect_uri = url_for("auth.github_callback", _external=True)
    return oauth.github.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/github/callback")
def github_callback():
    code = request.args.get("code")
    token = oauth.github.authorize_access_token()
    response = oauth.github.get("https://api.github.com/user")
    user_info = response.json()
    print("user_info", user_info)
    existing_user = db.users.find_one(
        {"provider": "github", "provider_id": user_info.get("id")}
    )
    if not existing_user:
        db.users.insert_one(
            {
                "provider": "github",
                "provider_id": user_info.get("id"),
                "username": user_info.get("name"),
                "email": user_info.get("email"),
                "profile_pic": user_info.get("avatar_url"),
            }
        )
    user_data = db.users.find_one(
        {"provider": "github", "provider_id": user_info.get("id")}
    )
    user = User(user_data)
    login_user(user)
    return redirect(url_for("index"))


@auth_bp.route("/login/facebook", methods=["GET", "POST"])
def facebook_auth():
    redirect_uri = url_for("auth.facebook_callback", _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/facebook/callback")
def facebook_callback():
    token = oauth.facebook.authorize_access_token()

    response = oauth.facebook.get("me?fields=id,name,email,picture")

    user_info = response.json()

    user_data = db.users.find_one(
        {"provider": "facebook", "provider_id": user_info.get("id")}
    )
    if not user_data:
        stored_user = db.users.insert_one(
            {
                "provider": "facebook",
                "provider_id": user_info.get("id"),
                "username": user_info.get("name"),
                "email": user_info.get("email"),
                "profile_pic": user_info["picture"]["data"]["url"],
            }
        )
        user_data = db.users.find_one({"username": user_info["name"]})

    user = User(user_data)
    login_user(user)
    return redirect(url_for("index"))
