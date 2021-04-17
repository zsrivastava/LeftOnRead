from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home_page.html")

@app.route("/booksearch") 
def book_search():
    return render_template("booksearch.html")

@app.route("/moviesearch")
def movie_search():
    return render_template("moviesearch.html")

@app.route("/tvsearch")
def tv_search():
    return render_template("tvsearch.html")

@app.route("/gamesearch")
def game_search():
    return render_template("gamesearch.html")

@app.route("/favorites")
def faves():
    return render_template("favorites.html")

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