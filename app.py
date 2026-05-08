from flask import Flask, redirect, render_template, request, url_for
import os
from bson import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, Length, URL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from authlib.integrations.flask_client import OAuth
import requests
from flask import session
import secrets

# loading the configuration from .env file
load_dotenv()


# making the application instance
app = Flask(__name__)
# storing the configuration in variables
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID")
app.config["GOOGLE_CLIENT_SECRET"] = os.getenv("GOOGLE_CLIENT_SECRET")
app.config["LINKEDIN_CLIENT_ID"] = os.getenv("LINKEDIN_CLIENT_ID")
app.config["LINKEDIN_CLIENT_SECRET"] = os.getenv("LINKEDIN_CLIENT_SECRET")
app.config["GITHUB_CLIENT_ID"] = os.getenv("GITHUB_CLIENT_ID")
app.config["GITHUB_CLIENT_SECRET"] = os.getenv("GITHUB_CLIENT_SECRET")
app.config["FACEBOOK_CLIENT_ID"] = os.getenv("FACEBOOK_CLIENT_ID")
app.config["FACEBOOK_CLIENT_SECRET"] = os.getenv("FACEBOOK_CLIENT_SECRET")


# connecting to the databases- database and collection creation
client = MongoClient(app.config["MONGO_URI"])
db = client["content"]
bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = "login"
oauth = OAuth(app)

oauth.register(
    name="google",
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
oauth.register(
    name="linkedin",
    client_id=app.config["LINKEDIN_CLIENT_ID"],
    client_secret=app.config["LINKEDIN_CLIENT_SECRET"],
    server_metadata_url="https://www.linkedin.com/oauth/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid profile email",
        "token_endpoint_auth_method": "client_secret_post",
    },
)
oauth.register(
    name="github",
    client_id=app.config["GITHUB_CLIENT_ID"],
    client_secret=app.config["GITHUB_CLIENT_SECRET"],
    server_metadata_url="https://github.com/login/oauth/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
# oauth.register(
#     name="facebook",
#     client_id=app.config["FACEBOOK_CLIENT_ID"],
#     client_secret=app.config["FACEBOOK_CLIENT_SECRET"],
#     access_token_url="https://graph.facebook.com/v22.0/oauth/access_token",
#     authorize_url="https://www.facebook.com/v22.0/dialog/oauth",
#     api_base_url="https://graph.facebook.com/v22.0/",
#     client_kwargs={
#         "scope": "email public_profile",
#     },
# )
oauth.register(
    name="facebook",
    client_id=app.config["FACEBOOK_CLIENT_ID"],
    client_secret=app.config["FACEBOOK_CLIENT_SECRET"],
    server_metadata_url="https://www.facebook.com/.well-known/openid-configuration/",
    client_kwargs={
        "scope": "openid email public_profile",
    },
)


class CommentForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3)],
        render_kw={"placeholder": "Enter your name"},
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    website = StringField(
        "Website",
        validators=[URL(require_tld=True, message="Please enter a valid URL.")],
        default="",
    )
    comment = TextAreaField("Comment", validators=[DataRequired(), Length(min=10)])
    image_url = StringField(
        "Image URL",
        validators=[URL(require_tld=True, message="Please enter a valid URL.")],
        default="",
    )
    submit = SubmitField("Submit")


class ContactForm(FlaskForm):

    name = StringField(
        "Name",
        validators=[DataRequired(), Length(min=3)],
        render_kw={"placeholder": "Your Name"},
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Your Email"},
    )
    subject = StringField(
        "Subject",
        validators=[DataRequired()],
        render_kw={"placeholder": "Your Subject"},
    )
    message = TextAreaField(
        "Message",
        validators=[DataRequired(), Length(min=5)],
        render_kw={"placeholder": "Your Message"},
    )
    submit = SubmitField("Submit")


class SignupForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3)],
        render_kw={"placeholder": "Enter your username"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=3)],
        render_kw={"placeholder": "Enter your password"},
    )
    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3)],
        render_kw={"placeholder": "Enter your username"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=3)],
        render_kw={"placeholder": "Enter your password"},
    )
    submit = SubmitField("Log In")


class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]
        self.provider = user_data["provider"]
        self.provider_id = user_data["provider_id"]
        self.email = user_data["email"]
        self.profile_pic = user_data["profile_pic"]


@login_manager.user_loader
def load_user(user_id):
    if user_id:
        user_data = db.users.find_one({"_id": ObjectId(user_id)})
        return User(user_data) if user_data else None
    else:
        print("user_id not found")


# routs started here
@app.route("/")
def index():
    collection1 = db["swiperData"]
    if collection1.count_documents({}) == 0:

        collection1.insert_many(
            [
                {
                    "title": "The Best Homemade Masks for Face (keep the Pimples Away)",
                    "description": "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Quidem neque est mollitia! Beatae minima assumenda repellat harum vero, officiis ipsam magnam obcaecati cumque maxime inventore repudiandae quidem necessitatibus rem atque.",
                    "image_url": url_for("static", filename="img/post-slide-1.jpg"),
                },
                {
                    "title": "10 Best Nutrition Tips for a Healthy Lifestyle",
                    "description": "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Quidem neque est mollitia! Beatae minima assumenda repellat harum vero, officiis ipsam magnam obcaecati cumque maxime inventore repudiandae quidem necessitatibus rem atque.",
                    "image_url": url_for("static", filename="img/post-slide-2.jpg"),
                },
                {
                    "title": "The Ultimate Guide to Homemade Masks for Face",
                    "description": "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Quidem neque est mollitia! Beatae minima assumenda repellat harum vero, officiis ipsam magnam obcaecati cumque maxime inventore repudiandae quidem necessitatibus rem atque.",
                    "image_url": url_for("static", filename="img/post-slide-3.jpg"),
                },
                {
                    "title": "5 Easy Ways to Stay Fit and Healthy",
                    "description": "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Quidem neque est mollitia! Beatae minima assumenda repellat harum vero, officiis ipsam magnam obcaecati cumque maxime inventore repudiandae quidem necessitatibus rem atque.",
                    "image_url": url_for("static", filename="img/post-slide-4.jpg"),
                },
            ]
        )

    data = collection1.find()

    return render_template("index.html", slides=data)


@app.route("/about")
def about():
    collection2 = db["teamMembers"]
    if collection2.count_documents({}) == 0:
        collection2.insert_many(
            [
                {
                    "name": "John Doe",
                    "position": "Founder & CEO",
                    "description": "Explicabo voluptatem mollitia et repellat qui dolorum quasi",
                    "image_url": url_for("static", filename="img/team/team-1.jpg"),
                },
                {
                    "name": "Jane Smith",
                    "position": "Chief Editor",
                    "description": "Explicabo voluptatem mollitia et repellat qui dolorum quasi",
                    "image_url": url_for("static", filename="img/team/team-2.jpg"),
                },
                {
                    "name": "Mike Johnson",
                    "position": "Content Manager",
                    "description": "Explicabo voluptatem mollitia et repellat qui dolorum quasi",
                    "image_url": url_for("static", filename="img/team/team-3.jpg"),
                },
                {
                    "name": "Emily Davis",
                    "position": "Marketing Specialist",
                    "description": "Explicabo voluptatem mollitia et repellat qui dolorum quasi",
                    "image_url": url_for("static", filename="img/team/team-4.jpg"),
                },
                {
                    "name": "David Wilson",
                    "position": "Graphic Designer",
                    "description": "Explicabo voluptatem mollitia et repellat qui dolorum quasi",
                    "image_url": url_for("static", filename="img/team/team-5.jpg"),
                },
                {
                    "name": "Sarah Brown",
                    "position": "Social Media Manager",
                    "description": "Explicabo voluptatem mollitia et repellat qui dolorum quasi",
                    "image_url": url_for("static", filename="img/team/team-6.jpg"),
                },
            ]
        )
    data = collection2.find()

    return render_template("about.html", team_members=data)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        collection = db["contact"]
        if collection.find_one({"email": form.email.data}) is None:
            collection.insert_one(
                {
                    "name": form.name.data,
                    "email": form.email.data,
                    "subject": form.subject.data,
                    "message": form.message.data,
                }
            )
            return redirect(url_for("contact"))

    return render_template("contact.html", form=form)


@app.route("/category")
def category():
    return render_template("category.html")


@app.route("/single-post", methods=["GET", "POST"])
def single_post():
    comments = list(db.comments.find())
    form = CommentForm()
    if form.validate_on_submit():
        db.comments.insert_one(
            {
                "username": form.username.data,
                "email": form.email.data,
                "website": form.website.data,
                "comment": form.comment.data,
                "image_url": form.image_url.data
                or url_for("static", filename="img/default.jpg"),
            }
        )
        return redirect(url_for("single_post"))

    count = db.comments.count_documents({})

    return render_template(
        "single-post.html", comments=comments, form=form, count=count
    )


@app.route("/starter-page")
def starter_page():
    return render_template("starter-page.html")


@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")


@app.route("/signup", methods=["GET", "POST"])
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
            return redirect(url_for("signup"))
        signup_data = db.users.insert_one(
            {"username": username, "password": hashed_password}
        )
        return redirect(url_for("login"))
    return render_template("signup.html", form=form)


@app.route("/login", methods=["GET", "POST"])
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


@app.route("/login/google", methods=["GET", "POST"])
def google_auth():
    redirect_uri = url_for("google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/auth/google/callback")
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


@app.route("/login/linkedin", methods=["GET", "POST"])
def linkedin_auth():
    redirect_uri = url_for("linkedin_callback", _external=True)
    return oauth.linkedin.authorize_redirect(redirect_uri)


@app.route("/auth/linkedin/callback")
def linkedin_callback():
    code = request.args.get("code")
    redirect_uri = url_for("linkedin_callback", _external=True)
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
    print("profile_pic", current_user.profile_pic)
    return redirect(url_for("index"))


@app.route("/login/github")
def github_auth():
    redirect_uri = url_for("github_callback", _external=True)
    return oauth.github.authorize_redirect(redirect_uri)


@app.route("/auth/github/callback")
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

@app.route("/login/facebook", methods=["GET", "POST"])
def facebook_auth():
    redirect_uri = url_for("facebook_callback", _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)


@app.route("/auth/facebook/callback")
def facebook_callback():
    code = request.args.get("code")
    token = oauth.facebook.authorize_access_token()
    response = oauth.facebook.get("https://openidconnect.googleapis.com/v1/userinfo")
    user_info = response.json()
    print(user_info)
    
    # user_data = db.users.find_one(
    #     {"provider": "facebook", "provider_id": user_info.get("sub")}
    # )
    # if not user_data:
    #     stored_user = db.users.insert_one(
    #         {
    #             "provider": "google",
    #             "provider_id": user_info.get("sub"),
    #             "username": user_info.get("name"),
    #             "email": user_info.get("email"),
    #             "profile_pic": user_info.get("picture"),
    #         }
    #     )
    #     user_data = db.users.find_one({"username": user_info["name"]})

    # user = User(user_data)
    # login_user(user)
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, port=9000)
