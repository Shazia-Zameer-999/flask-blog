from flask import Flask, redirect, render_template, url_for
from forms.forms import CommentForm, ContactForm
from database.db import db
from auth import auth_bp
from extensions import oauth, bootstrap, csrf, loginManager
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.register_blueprint(auth_bp)
loginManager.init_app(app)
csrf.init_app(app)
loginManager.login_view = "auth.login"
bootstrap.init_app(app)
oauth.init_app(app)

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

oauth.register(
    name="facebook",
    client_id=app.config["FACEBOOK_CLIENT_ID"],
    client_secret=app.config["FACEBOOK_CLIENT_SECRET"],
    access_token_url="https://graph.facebook.com/v22.0/oauth/access_token",
    authorize_url="https://www.facebook.com/v22.0/dialog/oauth",
    api_base_url="https://graph.facebook.com/v22.0/",
    client_kwargs={
        "scope": "email public_profile",
    },
)


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


if __name__ == "__main__":
    app.run(debug=True, port=9000)
