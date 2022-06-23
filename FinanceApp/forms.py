#! python3

from typing_extensions import Required
from flask import Flask
from flask_wtf import FlaskForm
from pyparsing import StringEnd
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import InputRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    username = StringField(
        "Username", validators=[InputRequired(message="Username is required")]
    )
    password = PasswordField(
        "Password",
        validators=[InputRequired(message="Password is required")],
    )
    rememberMe = BooleanField("Remember me")
    submit = SubmitField("Sign in")


class ResetPasswordForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[InputRequired(), Email(message="Wrongly formatted email address")],
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
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(message="Password is required"),
            Length(min=5, message="Password should be minimum 5 characters long"),
            EqualTo("repeatPassword", message="Passwords do not match"),
        ],
    )
    repeatPassword = PasswordField(
        "Repeat password",
        validators=[
            InputRequired(message="Password has to be repeated"),
        ],
    )
    firstName = StringField(
        "First name",
        validators=[
            InputRequired(message="First name is required"),
        ],
    )
    lastName = StringField(
        "Last name",
        validators=[
            InputRequired(message="Last name is required"),
        ],
    )
