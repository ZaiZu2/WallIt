from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import InputRequired, Email, EqualTo, Length, Regexp, Optional


class LoginForm(FlaskForm):
    username = StringField(
        "Username", validators=[InputRequired(message="Username is required")]
    )
    password = PasswordField(
        "Password", validators=[InputRequired(message="Password is required")]
    )
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Sign in")


class RequestPasswordForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[InputRequired(), Email(message="Wrongly formatted email address")],
    )


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(message="Password is required"),
            Length(min=5, message="Password should be minimum 5 characters long"),
            EqualTo("repeat_password", message="Passwords do not match"),
        ],
    )
    repeat_password = PasswordField(
        "Repeat password",
        validators=[
            InputRequired(message="Password has to be repeated"),
        ],
    )


class SignUpForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[
            InputRequired(message="Email is required"),
            Email(message="Wrongly formatted email address"),
        ],
    )
    username = StringField(
        "Username",
        validators=[
            InputRequired(message="Username is required"),
            Regexp(
                "^[A-Za-z0-9]+$",
                message="Username must be a single word consisting of alpha-numeric characters",
            ),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(message="Password is required"),
            Length(min=5, message="Password should be minimum 5 characters long"),
            EqualTo("repeat_password", message="Passwords do not match"),
        ],
    )
    repeat_password = PasswordField(
        "Repeat password",
        validators=[
            InputRequired(message="Password has to be repeated"),
        ],
    )
    first_name = StringField(
        "First name",
        validators=[
            Regexp(
                "^[A-Za-z]+$",
                message="First name must be a single word starting with a capital letter",
            ),
            Optional(),
        ],
    )
    last_name = StringField(
        "Last name",
        validators=[
            Regexp(
                "^[A-Za-z]+$",
                message="Last name must be a single word starting with a capital letter",
            ),
            Optional(),
        ],
    )
