# app.py

from bson.errors import InvalidId
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pymongo
import os
from bson import json_util, ObjectId
from flask_bcrypt import Bcrypt
from bbc_scraper import scrape_and_store_articles  # Import the scraping function

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'supersecretkey'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/db/users.db'  # Path to SQLite DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# MongoDB connection setup
mongo_host = os.getenv('MONGO_HOST', 'localhost')
mongo_port = int(os.getenv('MONGO_PORT', 27017))
mongo_client = pymongo.MongoClient(f"mongodb://{mongo_host}:{mongo_port}/")
db_mongo = mongo_client["scraper_db"]
collection = db_mongo["bbc_articles"]


# SQLAlchemy models for user management
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    saved_articles = db.Column(db.PickleType, default=[])

    def __repr__(self):
        return f'<User {self.username}>'


# Create database tables based on defined models
with app.app_context():
    db.create_all()


# Routes

@app.route('/')
def index():
    articles = collection.find()
    articles_list = list(articles)
    articles_data = [
        {**article, '_id': str(article['_id'])}  # Convert _id to string
        for article in articles_list
    ]
    return render_template('index.html', articles=articles_data)


@app.route('/details', methods=['GET'])
def article_details():
    article_id = request.args.get('id')
    if article_id:
        try:
            article_id = ObjectId(article_id)
            article = collection.find_one({'_id': article_id})
            if article:
                article_data = json_util.loads(json_util.dumps(article))
                return render_template('details.html', article=article_data)
            else:
                return jsonify({'error': 'Article not found'}), 404
        except InvalidId:
            return jsonify({'error': 'Invalid article ID'}), 400
    else:
        return jsonify({'error': 'Missing article ID'}), 400


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if User.query.filter_by(username=username).first():
            return 'Username already exists!'

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        return 'Invalid credentials!'
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if request.method == 'POST':
        scrape_and_store_articles()  # Call the scraping function
        return redirect(url_for('index'))
    return render_template('scrape.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
