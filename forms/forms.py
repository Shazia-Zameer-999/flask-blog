from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL, ValidationError


def validate_image_file(form, field):
    """Reject renamed non-image files by checking common image signatures."""
    upload = field.data
    if not upload or not upload.filename:
        return
    header = upload.stream.read(16)
    upload.stream.seek(0)
    is_image = (
        header.startswith(b"\xff\xd8\xff")
        or header.startswith(b"\x89PNG\r\n\x1a\n")
        or header.startswith((b"GIF87a", b"GIF89a"))
        or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
    )
    if not is_image:
        raise ValidationError("The selected file is not a valid image.")


class LoginForm(FlaskForm):
    identity = StringField("Username or email", validators=[DataRequired(), Length(min=3, max=120)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Keep me signed in")
    submit = SubmitField("Sign in")


class SignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create account")


class ProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=280)])
    profile_pic = StringField("Avatar URL", validators=[Optional(), URL(require_tld=True), Length(max=500)])
    profile_pic_file = FileField(
        "Or upload an avatar",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Upload a JPG, PNG, GIF, or WebP image."), validate_image_file],
    )
    submit = SubmitField("Save profile")

    def validate(self, extra_validators=None):
        valid = super().validate(extra_validators)
        if self.profile_pic.data and self.profile_pic_file.data and self.profile_pic_file.data.filename:
            message = "Choose either an avatar URL or a computer file, not both."
            self.profile_pic.errors.append(message)
            self.profile_pic_file.errors.append(message)
            return False
        return valid


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=5, max=140)])
    category = StringField("Category", validators=[DataRequired(), Length(min=2, max=40)])
    excerpt = TextAreaField("Summary", validators=[DataRequired(), Length(min=20, max=300)])
    body = TextAreaField("Article", validators=[DataRequired(), Length(min=100, max=30000)])
    image_url = StringField("Cover image URL", validators=[Optional(), URL(require_tld=True), Length(max=500)])
    image_file = FileField(
        "Or upload a cover image",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Upload a JPG, PNG, GIF, or WebP image."), validate_image_file],
    )
    published = BooleanField("Publish now", default=True)
    submit = SubmitField("Save article")

    def validate(self, extra_validators=None):
        valid = super().validate(extra_validators)
        if self.image_url.data and self.image_file.data and self.image_file.data.filename:
            message = "Choose either a cover URL or a computer file, not both."
            self.image_url.errors.append(message)
            self.image_file.errors.append(message)
            return False
        return valid


class CommentForm(FlaskForm):
    comment = TextAreaField("Join the conversation", validators=[DataRequired(), Length(min=3, max=1000)])
    submit = SubmitField("Post comment")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    subject = StringField("Subject", validators=[DataRequired(), Length(min=3, max=140)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=10, max=3000)])
    submit = SubmitField("Send message")
