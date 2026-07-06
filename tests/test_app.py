import pytest
from io import BytesIO

from app import create_app, slugify
from forms.forms import PostForm


@pytest.fixture()
def app():
    return create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test", "MONGO_URI": "mongodb://localhost:27017/test"})


def test_slugify_handles_punctuation_and_unicode():
    assert slugify("Café, Code & Clarity!") == "cafe-code-clarity"


def test_essential_routes_are_registered(app):
    rules = {rule.rule: rule.methods for rule in app.url_map.iter_rules()}
    assert "/" in rules
    assert "/articles" in rules
    assert "/articles/<slug>" in rules
    assert "POST" in rules["/articles/<slug>/delete"]
    assert "GET" not in rules["/logout"]


def test_security_defaults(app):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["MAX_CONTENT_LENGTH"] == 2 * 1024 * 1024


def test_computer_image_upload_validates_real_file_content(app):
    valid_data = {
        "title": "A useful article",
        "category": "Design",
        "excerpt": "A sufficiently detailed article summary.",
        "body": "A" * 120,
        "image_file": (BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 20), "cover.png"),
    }
    with app.test_request_context("/write", method="POST", data=valid_data):
        assert PostForm().validate()

    invalid_data = {
        "title": "A useful article",
        "category": "Design",
        "excerpt": "A sufficiently detailed article summary.",
        "body": "A" * 120,
        "image_file": (BytesIO(b"this is not an image"), "cover.png"),
    }
    with app.test_request_context("/write", method="POST", data=invalid_data):
        form = PostForm()
        assert not form.validate()
        assert "not a valid image" in form.image_file.errors[0]
