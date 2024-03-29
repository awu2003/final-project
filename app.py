import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

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

# configure upload folder
app.config["UPLOAD_FOLDER"] = "./static"


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
    """Shows user's website!"""
    user_id = session["user_id"]

    # Select all segments belonging to a user
    segments = db.execute("SELECT segment_type, content FROM segments WHERE user_id = ? ORDER BY location", user_id)
    design = db.execute("SELECT * FROM design WHERE user_id = ?", user_id)

    return render_template("index.html", segments=segments, design=design[0], len=len)


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

        # add design table row
        db.execute("INSERT INTO design (user_id) VALUES (?)", session["user_id"])

        # redirect to home page
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    """Hub for editing segments"""
    user_id = session["user_id"]
    if request.method == "GET":
        segments = db.execute("SELECT segment_type, location FROM segments WHERE user_id = ? ORDER BY location", user_id)
        return render_template("edit.html", segments=segments)
    else:
        # gets info from form
        if request.form.get('delete-button'):
            button_value = int(request.form['delete-button'])

            # gets number of segments
            segments_number = db.execute("SELECT segments_number FROM users WHERE user_id = ?", user_id)[0]['segments_number']

            # deletes segment in question
            db.execute("DELETE FROM segments WHERE user_id = ? AND location = ?", user_id, button_value)
            db.execute("UPDATE users SET segments_number = ? WHERE user_id = ?", segments_number - 1, user_id)

            # adjusts rest of segments in relation to segment to delete
            for i in range(1, segments_number + 1):
                if i > button_value:
                    db.execute("UPDATE segments SET location = ? WHERE location = ? AND user_id = ?", i - 1, i, user_id)

            segments = db.execute("SELECT segment_type, location FROM segments WHERE user_id = ? ORDER BY location", user_id)
            return render_template("edit.html", segments=segments)
        elif request.form.get('up-button'):
            button_value = int(request.form['up-button'])

            # swaps segments
            db.execute("UPDATE segments SET location = ? WHERE location = ? AND user_id = ?",
                       100000, button_value, user_id)
            db.execute("UPDATE segments SET location = ? WHERE location = ? AND user_id = ?",
                       button_value, button_value - 1, user_id)
            db.execute("UPDATE segments SET location = ? WHERE location = ? AND user_id = ?",
                       button_value - 1, 100000, user_id)
            
            segments = db.execute("SELECT segment_type, location FROM segments WHERE user_id = ? ORDER BY location", user_id)
            return render_template("edit.html", segments=segments)
        else:
            button_value = int(request.form['down-button'])

            # swaps segments
            db.execute("UPDATE segments SET location = ? WHERE location = ? AND user_id = ?",
                       100000, button_value, user_id)
            db.execute("UPDATE segments SET location = ? WHERE location = ? AND user_id = ?", 
                       button_value, button_value + 1, user_id)
            db.execute("UPDATE segments SET location = ? WHERE location = ? AND user_id = ?", 
                       button_value + 1, 100000, user_id)
            
            segments = db.execute("SELECT segment_type, location FROM segments WHERE user_id = ? ORDER BY location", user_id)
            return render_template("edit.html", segments=segments)


@app.route("/edit-header", methods=["GET", "POST"])
@login_required
def edit_header():
    if request.method == "GET":
        user_id = session["user_id"]
        # gets segment number to do conditional rendering on the html
        segments_number = db.execute("SELECT segments_number FROM users WHERE user_id = ?", user_id)[0]['segments_number']
        return render_template("edit-header.html", segments_number=segments_number)
    else:
        # get text from form
        header_text = request.form.get("header-text")
        if header_text == "":
            return apology("must enter text")
        
        # SQL time!
        user_id = session["user_id"]
        # update segments number for users table
        segments_number = db.execute("SELECT segments_number FROM users WHERE user_id = ?", user_id)[0]['segments_number']
        db.execute("UPDATE users SET segments_number = ? WHERE user_id = ?", segments_number + 1, user_id)
        
        # add segment to segments table
        db.execute("INSERT INTO segments (user_id, segment_type, content, location) VALUES (?, ?, ?, ?)",
                   user_id, "header", header_text, segments_number + 1)

        flash('Segment created!')
        return redirect("/")


@app.route("/edit-paragraph", methods=["GET", "POST"])
@login_required
def edit_paragraph():
    if request.method == "GET":
        user_id = session["user_id"]
        # gets segment number to do conditional rendering on the html
        segments_number = db.execute("SELECT segments_number FROM users WHERE user_id = ?", user_id)[0]['segments_number']
        return render_template("edit-paragraph.html", segments_number=segments_number)
    else:
        # get text from form
        paragraph_text = request.form.get("paragraph-text")
        if paragraph_text == "":
            return apology("must enter text")
        
        # SQL time!
        user_id = session["user_id"]
        # update segments number for users table
        segments_number = db.execute("SELECT segments_number FROM users WHERE user_id = ?", user_id)[0]['segments_number']
        db.execute("UPDATE users SET segments_number = ? WHERE user_id = ?", segments_number + 1, user_id)
        
        # add segment to segments table
        db.execute("INSERT INTO segments (user_id, segment_type, content, location) VALUES (?, ?, ?, ?)",
                   user_id, "paragraph", paragraph_text, segments_number + 1)
        flash('Segment created!')
        return redirect("/")


@app.route("/edit-image", methods=["GET", "POST"])
@login_required
def edit_image():
    if request.method == "GET":
        user_id = session["user_id"]
        # gets segment number to do conditional rendering on the html
        segments_number = db.execute("SELECT segments_number FROM users WHERE user_id = ?", user_id)[0]['segments_number']
        return render_template("edit-image.html", segments_number=segments_number)
    else:
        user_id = session["user_id"]
        segments_number = db.execute("SELECT segments_number FROM users WHERE user_id = ?", user_id)[0]['segments_number']
        if request.form.get('add-image'):
            # get text from form
            image_url = request.form.get("image-url")
            if image_url == "":
                return apology("must enter url")
            
            # SQL time!
            # update segments number for users table
            db.execute("UPDATE users SET segments_number = ? WHERE user_id = ?", segments_number + 1, user_id)
            
            # add segment to segments table
            db.execute("INSERT INTO segments (user_id, segment_type, content, location) VALUES (?, ?, ?, ?)",
                       user_id, "image", image_url, segments_number + 1)
            flash('Segment created!')
            return redirect("/")
        else:
            # code adapted from here: https://flask.palletsprojects.com/en/2.1.x/patterns/fileuploads/
            # check if the post request has the file part
            if 'file' not in request.files:
                flash("No file part")
                return redirect(request.url)
            file = request.files['file']
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # update user table
                db.execute("UPDATE users SET segments_number = ? WHERE user_id = ?", segments_number + 1, user_id)
                # add segment to segments table
                db.execute("INSERT INTO segments (user_id, segment_type, content, location) VALUES (?, ?, ?, ?)",
                           user_id, "image", "/static/" + filename, segments_number + 1)
                return redirect("/")


@app.route("/edit-video", methods=["GET", "POST"])
@login_required
def edit_video():
    """Add a video!"""
    if request.method == "GET":
        user_id = session["user_id"]
        # checks to see if user has enough segment allocations left
        segments_number = db.execute("SELECT segments_number FROM users WHERE user_id = ?", user_id)[0]['segments_number']
        return render_template("edit-video.html", segments_number=segments_number)
    else:
        user_id = session["user_id"]
        segments_number = db.execute("SELECT segments_number FROM users WHERE user_id = ?", user_id)[0]['segments_number']
        if request.form.get('add-video'):
            # get text from form
            video_url = request.form.get("video-url")
            # source for partition: https://www.stackvidhya.com/get-substring-of-string-python/
            video_url = video_url.partition("=")[2]
            # validate
            if video_url == "":
                return apology("must enter url")
            
            # SQL time!
            # update segments number for users table
            db.execute("UPDATE users SET segments_number = ? WHERE user_id = ?", segments_number + 1, user_id)
            
            # add segment to segments table
            db.execute("INSERT INTO segments (user_id, segment_type, content, location) VALUES (?, ?, ?, ?)",
                       user_id, "video", video_url, segments_number + 1)
            flash('Segment created!')
            return redirect("/")


@app.route("/edit-spotify", methods=["GET", "POST"])
@login_required
def edit_spotify():
    """Add a Spotify playlist!"""
    if request.method == "GET":
        user_id = session["user_id"]
        # checks to see if user has enough segment allocations left
        segments_number = db.execute("SELECT segments_number FROM users WHERE user_id = ?", user_id)[0]['segments_number']
        return render_template("edit-spotify.html", segments_number=segments_number)
    else:
        user_id = session["user_id"]
        segments_number = db.execute("SELECT segments_number FROM users WHERE user_id = ?", user_id)[0]['segments_number']
        if request.form.get('add-spotify'):
            # get text from form
            spotify_url = request.form.get("spotify-url")
            # source for partition: https://www.stackvidhya.com/get-substring-of-string-python/
            spotify_url = spotify_url.partition("com/")[2]
            spotify_url = spotify_url.partition("?")[0]
            # validate
            if spotify_url == "":
                return apology("must enter url")
            
            # SQL time!
            # update segments number for users table
            db.execute("UPDATE users SET segments_number = ? WHERE user_id = ?", segments_number + 1, user_id)
            
            # add segment to segments table
            db.execute("INSERT INTO segments (user_id, segment_type, content, location) VALUES (?, ?, ?, ?)",
                       user_id, "spotify", spotify_url, segments_number + 1)
            flash('Segment created!')
            return redirect("/")


@app.route("/friend-lookup", methods=["GET", "POST"])
@login_required
def friend_lookup():
    """Look up friend's website"""
    if request.method == "GET":
        return render_template("friend-lookup.html")
    else:
        # makes sure username exists
        friend_user = request.form.get("friend-lookup")
        if friend_user == "":
            return apology("must enter username")
        if len(db.execute("SELECT username FROM users WHERE username = ?", friend_user)) == 0:
            return apology("username does not exist")
        
        # select friend's segments
        segments = db.execute(
            "SELECT segment_type, content FROM segments WHERE user_id = (SELECT user_id FROM users WHERE username = ?) ORDER BY location", friend_user)
        # select friend's design
        design = db.execute("SELECT * FROM design WHERE user_id = (SELECT user_id FROM users WHERE username = ?)", friend_user)
        return render_template("friend-get.html", segments=segments, design=design[0], len=len)


@app.route("/my-friends", methods=["GET", "POST"])
@login_required
def my_friends():
    """Look up friend's website"""
    user_id = session["user_id"]
    if request.method == "GET":
        friends = db.execute("SELECT friend_username FROM friends WHERE user_id = ?", user_id)
        return render_template("my-friends.html", friends=friends)
    else:
        # makes sure username exists
        if request.form.get("add-friend"):
            friend_user = request.form.get("friend-lookup")
            if friend_user == "":
                return apology("must enter username")
            if len(db.execute("SELECT username FROM users WHERE username = ?", friend_user)) == 0:
                return apology("username does not exist")
            if len(db.execute("SELECT friend_username FROM friends WHERE user_id = ? AND friend_username = ?", user_id, friend_user)) > 0:
                return apology("friend already added")
            
            # add friend
            db.execute("INSERT INTO friends (user_id, friend_username) VALUES (?, ?)", user_id, friend_user)

            # reload page
            friends = db.execute("SELECT friend_username FROM friends WHERE user_id = ?", user_id)
            return render_template("my-friends.html", friends=friends)
        elif request.form.get("website-button"):
            friend_user = request.form['website-button']

            # select friend's segments
            segments = db.execute("SELECT segment_type, content FROM segments WHERE user_id = (SELECT user_id FROM users WHERE username = ?) ORDER BY location",
                                  friend_user)
            # select friend's design
            design = db.execute("SELECT * FROM design WHERE user_id = (SELECT user_id FROM users WHERE username = ?)", friend_user)
            return render_template("friend-get.html", segments=segments, design=design[0], len=len)
        else:
            friend_user = request.form['delete-button']
            db.execute("DELETE FROM friends WHERE user_id = ? AND friend_username = ?", user_id, friend_user)
            friends = db.execute("SELECT friend_username FROM friends WHERE user_id = ?", user_id)
            return render_template("my-friends.html", friends=friends)
            

@app.route("/edit-design", methods=["GET", "POST"])
@login_required
def edit_design():
    """A little more about this project!"""
    if request.method == "GET":
        return render_template("edit-design.html")
    else:
        user_id = session["user_id"]
        # get values from form
        background_color = request.form.get("background-color")
        header_font = request.form.get("header-font")
        header_size = request.form.get("header-size")
        paragraph_font = request.form.get("paragraph-font")
        paragraph_size = request.form.get("paragraph-size")

        if any(b == None for b in (background_color, header_font, header_size, paragraph_font, paragraph_size)):
            flash("Must complete form!")
            return redirect(request.url)
        # update design table
        db.execute("UPDATE design SET background_color = ?, header_font = ?, header_size = ?, paragraph_font = ?, paragraph_size = ? WHERE user_id = ?",
                   background_color, header_font, header_size, paragraph_font, paragraph_size, user_id)
        flash('Design updated!')
        return redirect("/")