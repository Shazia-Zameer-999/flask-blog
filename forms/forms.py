from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, Length, URL


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
