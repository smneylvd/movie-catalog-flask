import hashlib
import json

from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.session import Session
from sqlalchemy import insert, delete, func
import urllib.parse

server = Flask(__name__)
server.config[
    'SQLALCHEMY_DATABASE_URI'] = 'postgresql://xvjzihelipxhus:da6c7add058053763bd3506c6751d5b33853d89ad3d64ff2137e431aefd3f8bd@ec2-44-199-22-207.compute-1.amazonaws.com:5432/d30darjjfrh1g3'
server.config['SECRET_KEY'] = "123456789"
# db = create_engine(db_string)
db = SQLAlchemy(server)

with server.app_context():
    db.init_app(server)

sessionDB = Session(db)

import http.client

conn = http.client.HTTPSConnection("unogsng.p.rapidapi.com")

headers = {
    'X-RapidAPI-Key': "1b0a58516dmshb979dad82da135ap1cd9c3jsnf5e430b57a53",
    'X-RapidAPI-Host': "unogsng.p.rapidapi.com"
}


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(1000))
    email = db.Column(db.String(6000))
    password = db.Column(db.String(1000))


class Favourite(db.Model):
    __tablename__ = 'favourite'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    movie_id = db.Column(db.Integer)

    def get_movie(self):
        return db.session.query(Movie).filter_by(id=self.movie_id).first()


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(1000))
    img = db.Column(db.String(1000))
    vtype = db.Column(db.String(1000))
    nfid = db.Column(db.Integer)
    synopsis = db.Column(db.String(1000))
    avgrating = db.Column(db.Float)
    year = db.Column(db.Integer)
    runtime = db.Column(db.Float)
    imdbid = db.Column(db.String(1000))
    poster = db.Column(db.String(1000))
    imdbrating = db.Column(db.Float)
    clist = db.Column(db.String(1000))
    titledate = db.Column(db.Date)


def createUserDB():
    db.session.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id serial primary key,
        fullname text,
        email text,
        password text
    )
    ''')
    db.session.commit()


def createMovideDB():
    db.session.execute('''
    CREATE TABLE IF NOT EXISTS movie(
        id integer PRIMARY KEY ,
        title text,
        img text,
        vtype text,
        nfid integer,
        synopsis text,
        avgrating float,
        year integer,
        runtime float,
        imdbid text,
        poster text,
        imdbrating float,
        clist text,
        titledate date
    )
    ''')
    db.session.commit()


def createFavouriteDB():
    db.session.execute('''
    CREATE TABLE IF NOT EXISTS favourite(
        id serial primary key,
        user_id integer references users(id),
        movie_id integer references movie(id)
    )
    ''')
    db.session.commit()


@server.route('/')
def index():  # put application's code here
    if not session.get('user_id'):
        return redirect('/login')

    connUtelly = http.client.HTTPSConnection("utelly-tv-shows-and-movies-availability-v1.p.rapidapi.com")

    headersUtelly = {
        'X-RapidAPI-Key': "1b0a58516dmshb979dad82da135ap1cd9c3jsnf5e430b57a53",
        'X-RapidAPI-Host': "utelly-tv-shows-and-movies-availability-v1.p.rapidapi.com"
    }

    banners = []
    i = 0
    while i < 3:
        randMov = db.session.query(Movie).order_by(func.random()).limit(1).first()
        title = urllib.parse.quote_plus(randMov.title)
        print(title)
        connUtelly.request("GET", "/lookup?term=" + title, headers=headersUtelly)

        resUtelly = connUtelly.getresponse()
        dataUtelly = resUtelly.read()
        dataUtelly = json.loads(dataUtelly)
        try:
            banners.append({
                "movie": randMov,
                "image": dataUtelly['results'][0]['picture']
            })
        except:
            banners.append({
                "movie": randMov,
                "image": "https://utellyassets9-4.imgix.net/api/Images/1e6c8bf139b96ab0240715d0673bcb1f/Redirect?fit=crop&auto=compress&crop=faces,top"
            })
        i += 1

    movies = db.session.query(Movie).order_by(func.random())
    return render_template("index.html", movies=movies, banners=banners)


@server.route('/update-film-database', methods=["GET"])
def update_film_database():
    createMovideDB()
    movies = db.session.query(Movie)
    if not movies.first():

        conn.request("GET",
                     "/search?orderby=rating&audiosubtitle_andor=and&limit=100&audio=english&country_andorunique=unique&offset=0",
                     headers=headers)

        res = conn.getresponse()
        data = res.read()

        data = json.loads(data)

        for i in data['results']:
            # print(i)
            movie = Movie(
                id=i['id'],
                title=i['title'],
                img=i['img'],
                vtype=i['vtype'],
                nfid=i['nfid'],
                synopsis=i['synopsis'],
                avgrating=i['avgrating'],
                year=i['year'],
                runtime=i['runtime'],
                imdbid=i['imdbid'],
                poster=i['poster'],
                imdbrating=i['imdbrating'],
                clist=i['clist'],
                titledate=i['titledate'],
            )
            sessionDB.add(movie)
            sessionDB.commit()

    return redirect('/')


@server.route('/movie', methods=["GET"])
def product_details():
    prod_id = request.args.get('id')
    if not prod_id:
        return redirect('/')
    movie = db.session.query(Movie).filter_by(id=int(prod_id)).first()
    random_movies = db.session.query(Movie).order_by(func.random()).limit(5)
    print(random_movies)
    return render_template("details.html", movie=movie, recommendations=random_movies)


@server.route('/favourites')
def cart():
    createFavouriteDB()
    if not session.get('user_id'):
        return redirect('/login')
    favourite_movies = db.session.query(Favourite).filter_by(user_id=session.get('user_id'))
    print(favourite_movies.all())
    print(session.get('user_id'))
    for i in favourite_movies:
        print(i.get_movie())

    return render_template("favourites.html", products=favourite_movies)


@server.route('/remove-from-favourites', methods=['GET'])
def remove_form_favourites():
    if not session.get('user_id'):
        return redirect('/login')
    favourite_item = db.session.query(Favourite).filter_by(id=request.args.get('favourites_id')).first()
    print(favourite_item.id)
    db.session.delete(favourite_item)
    db.session.commit()
    return redirect('/favourites')


@server.route('/add-to-favourites', methods=['POST'])
def add_to_favourites():
    if not session.get('user_id'):
        return redirect('/login')
    if request.method == 'POST':
        p_id = request.form['movie_id']
        user_id = session.get('user_id')
        favourite = Favourite(user_id=user_id, movie_id=p_id)
        sessionDB.add(favourite)
        sessionDB.commit()
        return redirect('/movie?id=' + str(p_id))


@server.route('/logout', methods=["GET"])
def logout():
    session['user_id'] = None
    session['user_name'] = None
    session['user_email'] = None
    return redirect('/login')


@server.route('/login', methods=["GET", "POST"])
def login():
    msg = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = db.session.query(Users).filter_by(email=email).first()
        if user is None:
            msg = 'User not found'
            return render_template('login.html', error=msg)

        hashpws = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if user.password != hashpws:
            msg = 'Incorrect password'
            return render_template('login.html', error=msg)

        session['user_id'] = user.id
        session['user_name'] = user.fullname
        session['user_email'] = user.email
        return redirect('/')
    return render_template("login.html", error=msg)


@server.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form['first_name'] + ' ' + request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        repassword = request.form['re_password']
        user = db.session.query(Users).filter_by(email=email).first()
        if user:
            msg = {"text": 'Email already registered', "type": "danger"}
            return render_template('register.html', msg=msg)
        if password != repassword:
            msg = {"text": 'Passwords does not match', "type": "danger"}
            return render_template('register.html', msg=msg)
        hashpws = hashlib.sha256(password.encode('utf-8')).hexdigest()
        user = Users(fullname=fullname, email=email, password=hashpws)
        sessionDB.add(user)
        sessionDB.commit()
        msg = {"text": "Successfully registered!", "type": "success"}
        return render_template("register.html", msg=msg)

    return render_template("register.html")


if __name__ == '__main__':
    server.run(debug=True)
