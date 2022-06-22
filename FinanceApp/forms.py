#! python3

from typing_extensions import Required
from flask import Flask
from flask_wtf import FlaskForm
from pyparsing import StringEnd
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import InputRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField(
        "Password",
        validators=[InputRequired()],
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
        validators=[InputRequired(), Email(message="Wrongly formatted email address")],
    )
    username = StringField(
        "Username",
        validators=[
            InputRequired(),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(),
            Length(min=5, message="Password should be minimum 5 characters long"),
            EqualTo("repeatPassword", message="Passwords do not match"),
        ],
    )
    repeatPassword = PasswordField(
        "Repeat password",
        validators=[
            InputRequired(),
        ],
    )
    firstName = StringField(
        "Repeat password",
        validators=[
            InputRequired(),
        ],
    )
    lastName = StringField(
        "Repeat password",
        validators=[
            InputRequired(),
        ],
    )
