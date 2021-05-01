from flask import Flask, redirect, url_for, render_template, request, session
import os
import uuid
import hashlib
import pymysql.cursors
from functools import wraps
import time

app = Flask(__name__)
app.secret_key = "super secret key"

connection = pymysql.connect(host="localhost",
                             user="root",
                             password="root",
                             db="LOR",
                             charset="utf8mb4",
                             port=8889,
                             cursorclass=pymysql.cursors.DictCursor,
                             autocommit=True)

def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return dec

@app.route("/")
def open():
    return render_template("openpage.html")

@app.route("/home", methods=["GET"])
@login_required
def home():
    username = session["username"]
#    print(username)
    with connection.cursor() as cursor:
        query = "SELECT * FROM person WHERE username = %s"
        cursor.execute(query, username)
    data = cursor.fetchall()
    name = data[0]['firstName']
    return render_template("home_page.html", first_name = name)

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/registerAuth", methods=["POST"])
def registerAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPassword = requestData["password"]
        hashedPassword = hashlib.sha256(plaintextPassword.encode("utf-8")).hexdigest()
        firstName = requestData["firstName"]
        lastName = requestData["lastName"]
        
        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO person (username, password, firstName, lastName) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (username, plaintextPassword, firstName, lastName))
                session['username'] = username
        except pymysql.err.IntegrityError:
            error = "%s is already taken." % (username)
            return render_template('register.html', error=error)    
        
        return redirect(url_for("home"))

    error = "An error has occurred. Please try again."
    return render_template("register.html", error=error)

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/loginAuth", methods=["POST"])
def loginAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPassword = requestData["password"]
        hashedPassword = hashlib.sha256(plaintextPassword.encode("utf-8")).hexdigest()

        with connection.cursor() as cursor:
            query = "SELECT * FROM person WHERE username = %s AND password = %s"
            
            cursor.execute(query, (username,  plaintextPassword))
           
        data = cursor.fetchone()
        if data:
            session["username"] = username
            firstName = data['firstName']
            return redirect(url_for("home"))

        error = "Incorrect username or password."
        return render_template("login.html", error=error)

    error = "An unknown error has occurred. Please try again."
    return render_template("login.html", error=error)

@app.route("/logout", methods=["GET"])
def logout():
    session.pop("username")
    return redirect("/")

@app.route("/booksearch") 
def book_search():
    return render_template("booksearch.html")

@app.route("/moviesearch", methods=["GET"])
@login_required
def movie_search():
    username = session["username"]
    with connection.cursor() as cursor:
        query = "SELECT * FROM movies ORDER BY year DESC, title ASC, duration DESC"
        cursor.execute(query)
    data = cursor.fetchall()
    print(data)
    
    return render_template("moviesearch.html", data = data)

@app.route("/addFilmstoFavs", methods=["POST"])
@login_required
def films_to_faves():
    if request.files or request.data or request.form:
        requestData = request.form
        username = session["username"]
        titles = request.form.getlist("faves_add")
        media_type = "Movie"
    with connection.cursor() as cursor:
        for name in titles:
            query = "INSERT INTO favorites VALUES (%s, %s, %s)"        
            cursor.execute(query, (username, name, media_type))
    data = cursor.fetchall()
    message = "Successfully Added"
    return redirect(url_for("faves"))
#    return render_template("favorites.html", data = data)

@app.route("/tvsearch", methods=["GET"])
@login_required
def tv_search():
    username = session["username"]
    with connection.cursor() as cursor:
        query = "SELECT * FROM tvShows ORDER BY year DESC, RottenTomatoes DESC, title ASC"
        cursor.execute(query)
    data = cursor.fetchall()
    return render_template("tvsearch.html", data = data)

@app.route("/addShowstoFavs", methods=["POST"])
@login_required
def tvshows_to_faves():
    if request.files or request.data or request.form:
        requestData = request.form
        username = session["username"]
        titles = request.form.getlist("faves_add")
        media_type = "TV Show"
    with connection.cursor() as cursor:
        for name in titles:
            query = "INSERT INTO favorites VALUES (%s, %s, %s)"        
            cursor.execute(query, (username, name, media_type))
    data = cursor.fetchall()
    message = "Successfully Added"
    return redirect(url_for("faves"))
    #return render_template("favorites.html", data = data)

@app.route("/gamesearch", methods=["GET"])
@login_required
def game_search():
    username = session["username"]
    with connection.cursor() as cursor:
        query = "SELECT * FROM videoGames ORDER BY genre ASC, publisher ASC, title ASC, console ASC"
        cursor.execute(query)
    data = cursor.fetchall()
    return render_template("gamesearch.html", data = data)

@app.route("/addGamestoFavs", methods=["POST"])
@login_required
def games_to_faves():
    if request.files or request.data or request.form:
        requestData = request.form
        username = session["username"]
        titles = request.form.getlist("faves_add")
        media_type = "Video Game"
        for elem in titles:
            print(elem)
    with connection.cursor() as cursor:
        for name in titles:
            query = "INSERT INTO favorites VALUES (%s, %s, %s)"        
            cursor.execute(query, (username, name, media_type))
    data = cursor.fetchall()
    message = "Successfully Added"
    return redirect(url_for("faves"))
#    return render_template("favorites.html", data = data)

@app.route("/favorites")
def faves():
    username = session["username"]
    with connection.cursor() as cursor:
        query = "SELECT * FROM favorites WHERE user_id = %s ORDER BY type"
        cursor.execute(query, username)
    data = cursor.fetchall()
    return render_template("favorites.html", data = data)

@app.route("/deleteFromFaves", methods=["GET", "POST"])
@login_required
def delete_from_faves():
    if request.files or request.data or request.form:
        requestData = request.form
        username = session["username"]
        print(username)
        titles = request.form.getlist("faves_delete")
        with connection.cursor() as cursor:
            for name in titles:
                elem = []
                if(name[-5:]=="Movie"):
                    elem.append(name[:-5])
                    elem.append(name[-5:])
                elif(name[-7:] == "TV Show"):
                    elem.append(name[:-7])
                    elem.append(name[-7:])
                elif(name[-10:]=="Video Game"):
                    print(name[:-10])
                    elem.append(name[:-10])
                    elem.append(name[-10:])
                
                query = "DELETE FROM favorites WHERE user_id = %s AND title = %s AND type = %s"
                cursor.execute(query, (username, elem[0], elem[1]))
    return redirect(url_for("faves"))

@app.route("/wishlist")
def wish_list():
    return render_template("wishlist.html")

@app.route("/recs")
def recs():
    return render_template("recs.html")

@app.route("/admin")
def admin():
    return redirect(url_for("user", name='Admin!'))

if(__name__ == "__main__"):
    app.run(debug=True)