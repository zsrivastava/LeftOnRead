from flask import Flask, redirect, url_for, render_template, request, session
import os
import uuid
import hashlib
import pymysql.cursors
from functools import wraps
import time
import pandas as pd
import numpy as np

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

@app.route("/booksearch", methods=["GET"]) 
@login_required
def book_search():
    with connection.cursor() as cursor:
        query = "SELECT bookID, title, authors, language_code, num_pages, publication_date, publisher FROM books ORDER BY authors ASC, publication_date DESC, title ASC, publisher ASC"
        cursor.execute(query)
    data = cursor.fetchall()
    return render_template("booksearch.html", data = data)

@app.route("/moveBooks", methods=["POST"])
@login_required
def moveBooks():
    if request.files or request.data or request.form:
        requestData = request.form
        username = session["username"]
        bookID_faves = request.form.getlist("faves")
        bookID_wlist = request.form.getlist("wlist")
        media_type = "Book"
    with connection.cursor() as cursor:
        for book in bookID_faves:
            query1 = "SELECT title FROM books WHERE bookID = %s"
            cursor.execute(query1, book)
            data = cursor.fetchone()
            print(data)
            query2 = "INSERT INTO favorites VALUES (%s, %s, %s)"
            cursor.execute(query2, (username, data['title'], media_type))
        for book in bookID_wlist:
            query = "INSERT INTO wish_list VALUES (%s, %s)"
            cursor.execute(query, (username, book))
    return redirect(url_for("home"))

@app.route("/recsToList", methods=["POST"])
@login_required
def recsToBooks():
    if request.files or request.data or request.form:
        requestData = request.form
        username = session["username"]
        bookID_wlist = request.form.getlist("wlist")
        media_type = "Book"
    with connection.cursor() as cursor:
        for book in bookID_wlist:
            query = "INSERT INTO wish_list VALUES (%s, %s)"
            cursor.execute(query, (username, book))
    return redirect(url_for("home"))


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
                    elem.append(name[:-10])
                    elem.append(name[-10:])
                elif(name[-4:] == "Book"):
                    elem.append(name[:-4])
                    elem.append(name[-4:])
                
                query = "DELETE FROM favorites WHERE user_id = %s AND title = %s AND type = %s"
                cursor.execute(query, (username, elem[0], elem[1]))
    return redirect(url_for("faves"))

@app.route("/wishlist")
@login_required
def wish_list():
    username = session["username"]
    with connection.cursor() as cursor:
        query = "SELECT wish_list.bookID, title, authors, language_code, publication_date, publisher, num_pages, isbn13 FROM wish_list INNER JOIN books ON wish_list.bookID = books.bookID WHERE wish_list.username = %s ORDER BY authors ASC"
        cursor.execute(query, (username))
    data = cursor.fetchall()
    return render_template("wishlist.html", data = data)

@app.route("/moveFromList", methods=["POST"])
@login_required
def move_from_list():
    username = session["username"]
    bookID_faves = request.form.getlist("faves")
    bookID_remove = request.form.getlist("remove")
    with connection.cursor() as cursor:
        for book_id in bookID_faves:
            query2 = "SELECT title FROM wish_list INNER JOIN books ON wish_list.bookID = books.bookID WHERE wish_list.bookID = %s"
            cursor.execute(query2, book_id)
            data = cursor.fetchone()
            query2 = "INSERT INTO favorites VALUES (%s, %s, %s)"
            cursor.execute(query2, (username, data["title"], "Book"))
            query1 = "DELETE FROM wish_list WHERE bookID = %s AND username = %s"
            cursor.execute(query1, (book_id, username))
        for book_id in bookID_remove:
            query1 = "DELETE FROM wish_list WHERE bookID = %s AND username = %s"
            cursor.execute(query1, (book_id, username))
        return redirect(url_for("wish_list"))

@app.route("/recs", methods=["GET", "POST"])
@login_required
def recs():
    username = session["username"]
    with connection.cursor() as cursor:
        query = "SELECT * FROM favorites WHERE user_id = %s"
        cursor.execute(query, username)
        data = cursor.fetchall()
        types = []
        titles = []
        similar_interests = []
#        print(data)
        for elem in data:
            query = "SELECT user_id FROM favorites WHERE title = %s AND type = %s AND user_id != %s"
            cursor.execute(query, (elem['title'], elem['type'], username))
            data = cursor.fetchall()
            if(len(data) > 0):
                for i in range(len(data)):
                    similar_interests.append(data[i]['user_id'])
        book_ids = []
        for name in similar_interests:
            query2 = "SELECT bookID FROM favorites INNER JOIN books ON favorites.title = books.title WHERE favorites.user_id = %s AND bookID NOT IN (SELECT bookID FROM favorites INNER JOIN books ON favorites.title = books.title WHERE favorites.user_id = %s) AND bookID NOT IN (SELECT bookID FROM wish_list WHERE wish_list.username = %s)"
            cursor.execute(query2, (name, username, username))
            data = cursor.fetchall()
            if(len(data) > 0):
                for i in range(len(data)):
                    book_ids.append(data[i]['bookID'])
        book_ids = np.array(book_ids)
#        print(book_ids)
        book_ids = np.reshape(book_ids, (len(book_ids), 1))
        ones = np.ones(book_ids.shape)
        book_ids = np.hstack((book_ids, ones))
        df = pd.DataFrame(book_ids, columns = ['bookID', 'counts'])
        df = df.groupby('bookID').sum().reset_index()
#        df = df.sum().reset_index()
        df.sort_values('bookID', ascending=False)
        rec_ids = df['bookID'].to_numpy().astype(int)
#        print('Rec_Ids:', rec_ids)
        
        if(len(rec_ids > 10)):
            rec_ids = rec_ids[:10]
            
        dataset = []
        for book_id in rec_ids:
            query3 = "SELECT * FROM books WHERE bookID = %s"
            cursor.execute(query3, book_id)
            data = cursor.fetchall()
            dataset.append(data)   
        if(len(dataset) >= 5):
            return render_template("recs.html", data = dataset)
        else:
            query4 = "SELECT DISTINCT bookID, title, authors, language_code, publication_date, publisher, num_pages, isbn13 FROM books WHERE authors IN (SELECT authors FROM favorites INNER JOIN books ON favorites.title = books.title WHERE favorites.user_id = %s) AND title NOT IN (SELECT books.title FROM favorites INNER JOIN books ON favorites.title = books.title WHERE favorites.user_id = %s) AND title NOT IN (SELECT books.title FROM wish_list INNER JOIN books ON wish_list.bookID = books.bookID WHERE wish_list.username = %s)"
            cursor.execute(query4, (username, username, username))
            data = cursor.fetchall()
            for i in range(10):
                dataset.append([data[i]])
        
            return render_template("recs.html", data = dataset[:10])
        

        
    return render_template("recs.html")

@app.route("/admin")
def admin():
    return redirect(url_for("user", name='Admin!'))

if(__name__ == "__main__"):
    app.run(debug=True)