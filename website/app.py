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
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


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
    """Show portfolio of stocks"""
    # getting info for table from database
    user_id = session["user_id"]
    stocks = db.execute(
        "SELECT symbol, name, SUM(shares) FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", user_id)
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

    # adding info for prices, total price, and total
    total = 0.0
    for stock in stocks:
        price = lookup(stock["symbol"])["price"]
        stock["price"] = price
        stock["total_price"] = float(price) * int(stock["SUM(shares)"])
        total += stock["total_price"]

    return render_template("index.html", usd=usd, stocks=stocks, cash=cash, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # get input from form
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")

        try:
            shares = float(shares)
        except ValueError:
            if not shares.isnumeric():
                return apology("shares must be an integer")

        if shares < 1:
            return apology("shares must be positive")
        if not shares.is_integer():
            return apology("shares must be an integer")

        # check if symbol is valid
        quote = lookup(symbol)
        if not quote:
            return apology("not a valid symbol")
        name = quote["name"]

        # get price of single share
        price = quote["price"]

        # check if user can afford
        value = price * shares
        user_id = session["user_id"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]['cash']
        if (cash - value) < 0:
            return apology("not enough money")

        # SQL time!
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - value, user_id)
        db.execute("INSERT INTO transactions (user_id, symbol, name, shares, price) VALUES (?, ?, ?, ?, ?)",
                   user_id, symbol, name, shares, price)

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    transactions = db.execute("SELECT symbol, shares, price, timestamp FROM transactions WHERE user_id = ?", user_id)
    return render_template("history.html", usd=usd, transactions=transactions)


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
        session["user_id"] = rows[0]["id"]

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        # get input from form
        symbol = request.form.get("symbol")
        quote = lookup(symbol)

        # check if symbol is valud
        if not quote:
            return apology("not a valid symbol")

        # return page with information
        return render_template("quoted.html", symbol=quote["symbol"], name=quote["name"], price=usd(quote["price"]))
    else:
        return render_template("quote.html")


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
        session["user_id"] = db.execute("SELECT * FROM users WHERE username = ?", username)[0]["id"]

        # redirect to home page
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        # get input from form
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if shares < 1:
            return apology("shares must be positive", 403)

        # get price of single share
        quote = lookup(symbol)
        price = quote["price"]
        name = quote["name"]

        # check if user can sell that many shares
        user_id = session["user_id"]
        total_shares = int(db.execute("SELECT SUM(shares) FROM transactions WHERE user_id = ? AND symbol = ?",
                                      user_id, symbol)[0]["SUM(shares)"])
        if shares > total_shares:
            return apology("sellng too many shares")

        # make new variables and fix new ones in preparation for SQL time
        value = float(price * shares)
        shares = shares * (-1)

        # SQL time!
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]['cash']
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + value, user_id)
        db.execute("INSERT INTO transactions (user_id, symbol, name, shares, price) VALUES (?, ?, ?, ?, ?)",
                   user_id, symbol, name, shares, price)

        return redirect("/")
    else:
        owned = db.execute("SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0",
                           session["user_id"])
        return render_template("sell.html", owned=owned)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        # get money from form
        money = request.form.get("money")

        try:
            money = float(money)
        except ValueError:
            if money == "":
                return apology("must enter amount")
            if not money.isnumeric():
                return apology("amount must be a number")

        if money < 0:
            return apology("that is not a wise financial decision")

        # SQL time!
        user_id = session["user_id"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]['cash']
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + money, user_id)

        return redirect("/")
    else:
        return render_template("add.html")