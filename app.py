import os
import re
import unicodedata
from io import BytesIO
from datetime import datetime, timezone
import resend
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
    jsonify
)
from flask_login import current_user, login_required
from gridfs import GridFS
from gridfs.errors import NoFile
from pymongo import DESCENDING
from pymongo.errors import PyMongoError

from auth import auth_bp
from database.db import get_db, init_indexes
from extensions import bootstrap, csrf, loginManager, oauth
from forms.forms import CommentForm, ContactForm, PostForm, ProfileForm

load_dotenv()

resend.api_key = os.environ["RESEND_API_KEY"]
print("Resend API Key:", resend.api_key)  # Debugging line to check if the API key is loaded correctly

def slugify(value):
    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    )
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-me"),
        MONGO_URI=os.getenv("MONGO_URI"),
        MONGO_DB_NAME=os.getenv("MONGO_DB_NAME", "content"),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("FLASK_ENV") == "production",
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
    )
    for provider in ("GOOGLE", "LINKEDIN", "GITHUB", "FACEBOOK"):
        app.config[f"{provider}_CLIENT_ID"] = os.getenv(f"{provider}_CLIENT_ID")
        app.config[f"{provider}_CLIENT_SECRET"] = os.getenv(f"{provider}_CLIENT_SECRET")
    if test_config:
        app.config.update(test_config)
    loginManager.init_app(app)
    loginManager.login_view = "auth.login"
    loginManager.login_message_category = "warning"
    csrf.init_app(app)
    bootstrap.init_app(app)
    oauth.init_app(app)
    app.register_blueprint(auth_bp)
    _register_oauth(app)
    register_routes(app)
    register_errors(app)

    @app.context_processor
    def globals_():
        return {"current_year": datetime.now().year}

    @app.cli.command("init-db")
    def init_db_command():
        init_indexes()
        print("Database indexes created.")

    return app


def _register_oauth(app):
    configs = {
        "google": dict(
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        ),
        "linkedin": dict(
            server_metadata_url="https://www.linkedin.com/oauth/.well-known/openid-configuration",
            client_kwargs={
                "scope": "openid profile email",
            },
            token_endpoint_auth_method="client_secret_post",
        ),
        "github": dict(
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "read:user user:email"},
        ),
        "facebook": dict(
            access_token_url="https://graph.facebook.com/v22.0/oauth/access_token",
            authorize_url="https://www.facebook.com/v22.0/dialog/oauth",
            api_base_url="https://graph.facebook.com/v22.0/",
            client_kwargs={"scope": "email public_profile"},
        ),
    }
    for name, extra in configs.items():
        oauth.register(
            name=name,
            client_id=app.config.get(f"{name.upper()}_CLIENT_ID"),
            client_secret=app.config.get(f"{name.upper()}_CLIENT_SECRET"),
            **extra,
        )


def _oid(value):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        abort(404)


def _post_or_404(slug, include_drafts=False):
    query = {"slug": slug}
    if not include_drafts:
        query["published"] = True
    post = get_db().posts.find_one(query)
    if not post:
        abort(404)
    return post


def _attach_author_profiles(posts):
    """Attach each author's current name and avatar without per-post queries."""
    author_ids = {
        post.get("author_id")
        for post in posts
        if isinstance(post.get("author_id"), ObjectId)
    }
    if not author_ids:
        return posts
    profiles = {
        user["_id"]: user
        for user in get_db().users.find(
            {"_id": {"$in": list(author_ids)}},
            {"username": 1, "profile_pic": 1},
        )
    }
    for post in posts:
        profile = profiles.get(post.get("author_id"))
        if profile:
            post["author_name"] = profile.get(
                "username", post.get("author_name", "Reader")
            )
            post["author_avatar"] = profile.get("profile_pic", "")
    return posts


def _save_image(file_storage, prefix):
    """Persist a validated image in MongoDB so it works on serverless hosts."""
    if not file_storage or not file_storage.filename:
        return None
    extension = os.path.splitext(file_storage.filename)[1].lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    image_id = GridFS(get_db(), collection="images").put(
        file_storage.stream,
        filename=f"{prefix}{extension}",
        content_type=mime_types[extension],
        uploaded_at=datetime.now(timezone.utc),
    )
    return url_for("media", image_id=str(image_id))


def _delete_image(image_url):
    """Remove only MongoDB images managed by this app; external URLs are untouched."""
    marker = "/media/"
    if not image_url or marker not in image_url:
        return
    try:
        GridFS(get_db(), collection="images").delete(
            ObjectId(image_url.rsplit(marker, 1)[1].split("?", 1)[0])
        )
    except (InvalidId, TypeError):
        return


def register_routes(app):
    @app.get("/media/<image_id>")
    def media(image_id):
        try:
            image = GridFS(get_db(), collection="images").get(_oid(image_id))
        except NoFile:
            abort(404)
        response = send_file(
            BytesIO(image.read()), mimetype=image.content_type, max_age=31536000
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'none'; sandbox"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/")
    def index():
        posts = _attach_author_profiles(
            list(
                get_db()
                .posts.find({"published": True})
                .sort("created_at", DESCENDING)
                .limit(7)
            )
        )
        return render_template(
            "index.html", posts=posts, featured=posts[0] if posts else None
        )

    @app.get("/articles")
    @app.get("/category")
    def category():
        page = max(request.args.get("page", 1, type=int), 1)
        query_text = request.args.get("q", "").strip()[:100]
        category_name = request.args.get("category", "").strip()[:40]
        query = {"published": True}
        if query_text:
            query["$text"] = {"$search": query_text}
        if category_name:
            query["category"] = category_name
        per_page = 6
        total = get_db().posts.count_documents(query)
        posts = _attach_author_profiles(
            list(
                get_db()
                .posts.find(query)
                .sort("created_at", DESCENDING)
                .skip((page - 1) * per_page)
                .limit(per_page)
            )
        )
        categories = get_db().posts.distinct("category", {"published": True})
        return render_template(
            "category.html",
            posts=posts,
            categories=sorted(filter(None, categories)),
            page=page,
            pages=max(1, (total + per_page - 1) // per_page),
            total=total,
            query_text=query_text,
            selected_category=category_name,
        )

    @app.route("/articles/<slug>", methods=["GET", "POST"])
    def article(slug):
        post = _post_or_404(slug)
        _attach_author_profiles([post])
        form = CommentForm()
        if form.validate_on_submit():
            if not current_user.is_authenticated:
                flash("Sign in to join the conversation.", "warning")
                return redirect(url_for("auth.login", next=request.path))
            get_db().comments.insert_one(
                {
                    "post_id": post["_id"],
                    "user_id": ObjectId(current_user.id),
                    "username": current_user.username,
                    "avatar_url": current_user.profile_pic,
                    "body": form.comment.data.strip(),
                    "created_at": datetime.now(timezone.utc),
                }
            )
            flash("Your comment is live.", "success")
            return redirect(url_for("article", slug=slug, _anchor="comments"))
        comments = list(
            get_db()
            .comments.find({"post_id": post["_id"]})
            .sort("created_at", DESCENDING)
        )
        commenter_ids = {
            comment.get("user_id")
            for comment in comments
            if isinstance(comment.get("user_id"), ObjectId)
        }
        commenter_profiles = (
            {
                user["_id"]: user
                for user in get_db().users.find(
                    {"_id": {"$in": list(commenter_ids)}},
                    {"username": 1, "profile_pic": 1},
                )
            }
            if commenter_ids
            else {}
        )
        for comment in comments:
            profile = commenter_profiles.get(comment.get("user_id"))
            if profile:
                comment["username"] = profile.get(
                    "username", comment.get("username", "Reader")
                )
                comment["avatar_url"] = profile.get("profile_pic", "")
        return render_template(
            "single-post.html", post=post, comments=comments, form=form
        )

    @app.route("/single-post", methods=["GET", "POST"])
    def single_post():
        post = get_db().posts.find_one(
            {"published": True}, sort=[("created_at", DESCENDING)]
        )
        if not post:
            return redirect(url_for("category"))
        return redirect(url_for("article", slug=post["slug"]))

    @app.route("/write", methods=["GET", "POST"])
    @login_required
    def create_post():
        form = PostForm()
        if form.validate_on_submit():
            slug = slugify(form.title.data)
            base, suffix = slug, 1
            while get_db().posts.find_one({"slug": slug}):
                suffix += 1
                slug = f"{base}-{suffix}"
            image_url = (
                _save_image(form.image_file.data, "cover")
                or (form.image_url.data or "").strip()
            )
            get_db().posts.insert_one(_post_data(form, slug, image_url))
            flash(
                "Article published." if form.published.data else "Draft saved.",
                "success",
            )
            return redirect(
                url_for("article", slug=slug)
                if form.published.data
                else url_for("profile")
            )
        return render_template("post_form.html", form=form, title="Write an article")

    @app.route("/articles/<slug>/edit", methods=["GET", "POST"])
    @login_required
    def edit_post(slug):
        post = _post_or_404(slug, include_drafts=True)
        if str(post.get("author_id")) != current_user.id and not current_user.is_admin:
            abort(403)
        form_values = dict(post)
        if "/media/" in form_values.get("image_url", ""):
            form_values["image_url"] = ""
        form = PostForm(
            obj=type("Post", (), form_values) if request.method == "GET" else None
        )
        if form.validate_on_submit():
            uploaded_url = _save_image(form.image_file.data, "cover")
            image_url = (
                uploaded_url
                or (form.image_url.data or "").strip()
                or post.get("image_url", "")
            )
            data = _post_data(form, post["slug"], image_url)
            data.pop("created_at", None)
            get_db().posts.update_one({"_id": post["_id"]}, {"$set": data})
            if uploaded_url and post.get("image_url") != uploaded_url:
                _delete_image(post.get("image_url"))
            flash("Article updated.", "success")
            return redirect(
                url_for("article", slug=post["slug"])
                if form.published.data
                else url_for("profile")
            )
        return render_template(
            "post_form.html", form=form, title="Edit article", post=post
        )

    @app.post("/articles/<slug>/delete")
    @login_required
    def delete_post(slug):
        post = _post_or_404(slug, include_drafts=True)
        if str(post.get("author_id")) != current_user.id and not current_user.is_admin:
            abort(403)
        get_db().comments.delete_many({"post_id": post["_id"]})
        get_db().posts.delete_one({"_id": post["_id"]})
        _delete_image(post.get("image_url"))
        flash("Article deleted.", "info")
        return redirect(url_for("profile"))

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        database = get_db()
        user = database.users.find_one({"_id": ObjectId(current_user.id)})
        form_values = dict(user)
        if "/media/" in form_values.get("profile_pic", ""):
            form_values["profile_pic"] = ""
        form = ProfileForm(
            obj=type("Profile", (), form_values) if request.method == "GET" else None
        )
        if form.validate_on_submit():
            conflict = database.users.find_one(
                {
                    "_id": {"$ne": user["_id"]},
                    "$or": [
                        {"username": form.username.data.lower()},
                        {"email": form.email.data.lower()},
                    ],
                }
            )
            if conflict:
                flash("That username or email is already in use.", "danger")
            else:
                uploaded_url = _save_image(form.profile_pic_file.data, "avatar")
                profile_pic = (
                    uploaded_url
                    or (form.profile_pic.data or "").strip()
                    or user.get("profile_pic", "")
                )
                database.users.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "username": form.username.data.strip().lower(),
                            "email": form.email.data.strip().lower(),
                            "bio": (form.bio.data or "").strip(),
                            "profile_pic": profile_pic,
                        }
                    },
                )
                if uploaded_url and user.get("profile_pic") != uploaded_url:
                    _delete_image(user.get("profile_pic"))
                flash("Profile updated.", "success")
                return redirect(url_for("profile"))
        posts = list(
            database.posts.find({"author_id": user["_id"]}).sort(
                "created_at", DESCENDING
            )
        )
        return render_template("profile.html", form=form, posts=posts)

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        form = ContactForm()
        
        # Check if this is an AJAX/Fetch request expecting JSON
        is_ajax = request.headers.get("Accept") == "application/json"

        if form.validate_on_submit():
            try:
                message_data = {
                    "name": form.name.data.strip(),
                    "email": form.email.data.lower().strip(),
                    "subject": form.subject.data.strip(),
                    "message": form.message.data.strip(),
                    "created_at": datetime.now(timezone.utc),
                    "status": "new",
                }
                
                get_db().messages.insert_one(message_data)
                print(f"Message saved for: {message_data['email']}") 

                params: resend.Emails.SendParams = {
                    "from": "Shazia Zameer <onboarding@resend.dev>",
                    "to": ["shaziazameer7867@gmail.com"],
                    "subject": message_data["subject"],
                    "html": f"<strong>{message_data['message']}</strong>",
                }
                
                resend.Emails.send(params)

                if is_ajax:
                    return jsonify({"status": "success", "message": "Thanks — your message has reached us."}), 200

                flash("Thanks — your message has reached us.", "success")
                return redirect(url_for("contact"))
                
            except Exception as e:
                print(f"Error processing contact form: {e}")
                if is_ajax:
                    return jsonify({"status": "error", "message": "Sorry, something went wrong. Please try again."}), 500
                
                flash("Sorry, something went wrong while sending your message. Please try again.", "error")

        # If form validation fails on a POST request
        if request.method == "POST" and is_ajax:
            return jsonify({"status": "invalid", "errors": form.errors}), 400

        return render_template("contact.html", form=form)

    @app.get("/about")
    def about():
        return render_template("about.html")

    @app.get("/privacy-policy")
    def privacy_policy():
        return render_template("privacy_policy.html")

    def _post_data(form, slug, image_url):
        return {
            "title": form.title.data.strip(),
            "slug": slug,
            "category": form.category.data.strip().title(),
            "excerpt": form.excerpt.data.strip(),
            "body": form.body.data.strip(),
            "image_url": image_url,
            "published": form.published.data,
            "author_id": ObjectId(current_user.id),
            "author_name": current_user.username,
            "author_avatar": current_user.profile_pic,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }


def register_errors(app):
    @app.errorhandler(403)
    def forbidden(error):
        return (
            render_template(
                "error.html",
                code=403,
                title="Not allowed",
                message="You don't have permission to do that.",
            ),
            403,
        )

    @app.errorhandler(404)
    def not_found(error):
        return (
            render_template(
                "error.html",
                code=404,
                title="Page not found",
                message="That page wandered off the map.",
            ),
            404,
        )

    @app.errorhandler(413)
    def too_large(error):
        return (
            render_template(
                "error.html",
                code=413,
                title="Request too large",
                message="Please submit a smaller request.",
            ),
            413,
        )

    @app.errorhandler(PyMongoError)
    def database_error(error):
        app.logger.exception("Database request failed")
        return (
            render_template(
                "error.html",
                code=503,
                title="We'll be right back",
                message="The content service is temporarily unavailable.",
            ),
            503,
        )


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=int(os.getenv("PORT", "9000")))
