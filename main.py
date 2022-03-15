from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, HiddenField
from wtforms.validators import DataRequired
from typing import Callable
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

# SQLAlchemy settings
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Bootstrap setup
Bootstrap(app)
MOVIES_DB_URL = "https://api.themoviedb.org/3"
MOVIES_API_KEY = os.environ.get("MOVIES_API_KEY")

#  FORMS

# Editrateform class

class EditForm(FlaskForm):
    edit_rating = DecimalField(label="Your rating out of 10 e.g. 9.5", validators=[DataRequired()])
    edit_review = StringField(label="Your Review", validators=[DataRequired()])
    # hidden = HiddenField()
    submit = SubmitField()

# Addmovieform class
class AddMovieForm(FlaskForm):
    movie_title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

# SQLAlchemy class
class MySQLAlchemy(SQLAlchemy):
    Column: Callable
    String: Callable
    Float: Callable
    Integer: Callable

db = MySQLAlchemy(app)

class Movies(db.Model):
    __table_name__ = "Movie Table"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

# database table create
# db.create_all()

# home route
@app.route("/")
def home():
    all_movies = Movies.query.order_by(Movies.rating).all() # creates a list of all ratings from last/smallest to biggest.
    all_movies.reverse() # reverses the list from first to last
    num = 0
    for movie in all_movies:
        movie_update = Movies.query.get(movie.id)
        num += 1
        movie_update.ranking = num
        db.session.commit()
    return render_template("index.html", movies=all_movies)


# add movie
@app.route("/add", methods=["POST", "GET"])
def add_movie():
    add_form = AddMovieForm()
    if add_form.validate_on_submit():
        movie_name = add_form.movie_title.data
        print(movie_name)
        movie_params = {
            "api_key": MOVIES_API_KEY,
            "query": movie_name,
        }
        response = requests.get(url=f"{MOVIES_DB_URL}/search/movie", params=movie_params)
        movie_data = response.json()["results"]
        return render_template("select.html",  movies=movie_data)
    return render_template("add.html", add_form=add_form)

# add movie to database
@app.route("/add_database", methods=["POST", "GET"])
def add_to_database():
    movie_id = request.args.get('id')
    movie_id_params = {
        "api_key": MOVIES_API_KEY,
    }
    response = requests.get(url=f"{MOVIES_DB_URL}/movie/{movie_id}", params=movie_id_params) # get movie  details
    new_movie_data = response.json()
    new_movie = Movies(
        title=new_movie_data["title"],
        year=new_movie_data["release_date"].split("-")[0],
        description=new_movie_data["overview"],
        img_url="https://image.tmdb.org/t/p/w500"+new_movie_data["poster_path"]
    )
    db.session.add(new_movie)
    db.session.commit()
    all_movies = db.session.query(Movies).all()
    for movie in all_movies:
        if movie.title == new_movie_data["title"]:
            return redirect(url_for('edit_movie', id=movie.id))


# edit movie
@app.route("/edit", methods=["POST", "GET"])
def edit_movie():
    edit_form = EditForm()  # editmovie form
    new_movie = request.args.get("id")  # movie id from database
    if edit_form.validate_on_submit():
        new_rating = edit_form.edit_rating.data
        new_review = edit_form.edit_review.data
        new_movie_update = Movies.query.get(new_movie)
        new_movie_update.rating = new_rating
        new_movie_update.review = new_review
        db.session.commit()
        return redirect(url_for('home'))
    all_movies = db.session.query(Movies).all()
    for movie in all_movies:
        if movie.id == int(new_movie):
            return render_template("edit.html", edit_form=edit_form, movie_title=movie.title)

# delete movie
@app.route("/delete", methods=["POST", "GET"])
def delete_movie():
    new_movie = request.args.get("id")
    new_movie_delete = Movies.query.get(new_movie)
    db.session.delete(new_movie_delete)
    db.session.commit()
    return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)
