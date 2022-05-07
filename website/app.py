import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///database.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # get inputs from form
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # check that everything is correctly filled out
        if username == "":
            return apology("must provide username")
        if len(db.execute("SELECT username FROM users WHERE username = ?", username)) > 0:
            return apology("username is already in use")
        if password == "":
            return apology("must provide password")
        if confirmation == "":
            return apology("must confirm password")
        if password != confirmation:
            return apology("password does not match")

        # save username and password hash
        db.execute("INSERT INTO users(username, hash) VALUES(?, ?)", username, generate_password_hash(password))

        # set current user session
        session["user_id"] = db.execute("SELECT * FROM users WHERE username = ?", username)[0]["user_id"]

        # redirect to home page
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    """Hub for editing segments"""
    if request.method == "GET":
        return render_template("edit.html")

@app.route("/edit-header", methods=["GET", "POST"])
@login_required
def edit_header():
    if request.method == "GET":
        return render_template("edit-header.html")

@app.route("/edit-paragraph", methods=["GET", "POST"])
@login_required
def edit_paragraph():
    if request.method == "GET":
        return render_template("edit-paragraph.html")
    #else:


@app.route("/edit-image", methods=["GET", "POST"])
@login_required
def edit_image():
    if request.method == "GET":
        return render_template("edit-image.html")

@app.route("/about", methods=["GET"])
@login_required
def about():
    """A little more about this project!"""
    return render_template("about.html")