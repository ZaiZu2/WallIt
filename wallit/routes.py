#! python3


from sqlalchemy import select, func, desc
from wallit import app, db, logger
from wallit.forms import LoginForm, SignUpForm, ResetPasswordForm
from wallit.models import Transaction, User, Bank, Category

from flask import redirect, url_for, render_template, flash, request
from flask_login import current_user, login_required, login_user, logout_user

from datetime import datetime


@app.route("/")
@login_required
def index():
    currencies = ["CZK", "PLN", "EUR", "USD"]
    categories = ["Groceries", "Salary", "Entertainment", "Hobby", "Restaurant", "Rent"]
    banks = ["Equabank", "mBank", "Revolut"]

    return render_template(
        "index.html",
        currencies=currencies,
        categories=categories,
        banks=banks,
        current_user=current_user._get_current_object(),
    )


@app.route("/welcome", methods=["GET"])
def welcome():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    login_form = LoginForm()
    sign_up_form = SignUpForm()
    reset_password_form = ResetPasswordForm()

    return render_template(
        "welcome.html",
        login_form=login_form,
        sign_up_form=sign_up_form,
        reset_password_form=reset_password_form,
    )


@app.route("/login", methods=["POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).first()
        if user is None or not user.check_password(login_form.password.data):
            flash("Invalid username or password", "login_message")
            return redirect(url_for("welcome"))

        login_user(user, remember=login_form.remember_me.data)
        return redirect(url_for("index"))

    # Reassing form.errors to flash as they will be inaccessible after after redirection
    for field in login_form._fields.values():
        for error in field.errors:
            flash(error, "login_message")
    return redirect(url_for("welcome"))


@app.route("/account/reset", methods=["POST"])
def reset_password():
    reset_password_form = ResetPasswordForm()
    if reset_password_form.validate_on_submit():
        if User.query.filter_by(email=reset_password_form.email.data).first():
            # send email with password reset form
            flash("Email with password reset form was sent", "reset_password_message")
            return redirect(url_for("welcome"))

        flash("Account with given email does not exist", "reset_password_message")

    # Reassign form.errors to flash as they will be inaccessible after after redirection
    for field in reset_password_form._fields.values():
        for error in field.errors:
            flash(error, "reset_password_message")
    return redirect(url_for("welcome"))


@app.route("/account/new", methods=["POST"])
def sign_up():
    sign_up_form = SignUpForm()
    if sign_up_form.validate_on_submit():
        if User.query.filter_by(username=sign_up_form.username.data).first():
            flash("Username is already used, 'sign_up_message'")
            return redirect(url_for("welcome"))
        if User.query.filter_by(email=sign_up_form.email.data).first():
            flash("Email is already used", "sign_up_message")
            return redirect(url_for("welcome"))

        new_user = User(
            username=sign_up_form.username.data,
            email=sign_up_form.email.data,
            password=sign_up_form.password.data,
            first_name=sign_up_form.first_name.data,
            last_name=sign_up_form.last_name.data,
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully", "sign_up_message")
        return redirect(url_for("welcome"))

    # Reassing form.errors to flash as they will be inaccessible after after redirection
    for field in sign_up_form._fields.values():
        for error in field.errors:
            flash(error, "sign_up_message")
    return redirect(url_for("welcome"))


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("welcome"))


@app.route("/api/transactions")
@login_required
def populate_transaction_table():
    """Generate serialized transaction records used for populating Transaction Table

    Returns:
        dict: serialized transaction data and transaction count
    """

    # Dictionary mapping queried values to the keys used for serialization
    table_map = {
        "info": Transaction.info,
        "title": Transaction.title,
        "amount": Transaction.amount,
        "currency": Transaction.currency,
        "date": Transaction.transaction_date,
        "place": Transaction.place,
        "category": Category.name,
        "bank": Bank.name,
    }

    # Build a base query
    query = (
        select([db_fieldname for db_fieldname in table_map.values()])
        .filter_by(user_id=current_user.id)
        .select_from(Transaction)
        .join(Bank)
        .join(Category)
    )
    # Query for number of Transactions found
    count_query = select(func.count(Transaction.id)).filter_by(user_id=current_user.id)

    # Apply search phrase to the base queries
    search = request.args.get("search")
    if search:
        query = query.filter(
            db.or_(
                table_map["info"].ilike(f"%{search}%"),
                table_map["title"].ilike(f"%{search}%"),
            )
        )
        count_query = count_query.filter(
            db.or_(
                table_map["info"].ilike(f"%{search}%"),
                table_map["title"].ilike(f"%{search}%"),
            )
        )

    # Apply sorting to the base query
    sort = request.args.get("sort")
    if sort:
        ordered_columns = []
        for substring in sort.split(","):
            direction = substring[0]
            column_name = substring[1:]
            column = table_map[column_name]

            if direction == "-":
                column = column.desc()
            ordered_columns.append(column)

        if ordered_columns:
            query = query.order_by(*ordered_columns)

    # Pagination
    start = request.args.get("start", type=int)
    length = request.args.get("limit", type=int)
    query = query.offset(start).limit(length)

    # Query execution
    total_rows = db.session.execute(count_query).scalar()
    results = db.session.execute(query).all()
    logger.debug(query.compile().string)
    logger.debug(count_query.compile().string)

    # Serializing data received from the DB
    table_rows = []
    for row in results:
        result_dict = {}
        for name, transaction in zip(table_map.keys(), row):
            if isinstance(transaction, datetime):
                result_dict[name] = transaction.strftime(f"%Y/%m/%d")
            else:
                result_dict[name] = transaction
        table_rows.append(result_dict)

    return {"transactions": table_rows, "total": total_rows}
