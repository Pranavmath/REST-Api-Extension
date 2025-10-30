import tensorflow_hub as hub
from flask import Flask, jsonify, request
from os import path
from sqlalchemy import desc
from scipy import spatial
from bs4 import BeautifulSoup
import requests
from models import db, Leaderboard, DB_NAME
import tensorflow as tf
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    create_database(app)

    return app


def create_database(app):
    if not path.exists(DB_NAME):
        db.create_all(app=app)
        print('Created Database!')


app = create_app()

#embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")

embed = tf.saved_model.load("universal-sentence-encoder")


def get_2_embeddings(text1, text2):
    emb1 = embed([text1])
    emb2 = embed([text2])
    return [emb1, emb2]


def cosine_similarity(vec1, vec2):
    return 1 - spatial.distance.cosine(vec1, vec2)


@app.route("/leaderboard", methods=["POST", "GET"])
def leaderboard():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        name = request.form.get("name")
        coins = request.form.get("coins")
        user_search = Leaderboard.query.filter_by(id=user_id).first()

        current_leaderboard = []

        if user_search:
            user_search.coins = coins
            db.session.commit()

            leaderboard_user = Leaderboard.query.order_by(desc(Leaderboard.coins)).limit(5).all()
            for u in leaderboard_user:
                current_leaderboard.append((u.name, u.coins))

            return jsonify(userid=user_search.id, leaderboard=current_leaderboard)
        else:
            user = Leaderboard(name=name, coins=coins)
            db.session.add(user)
            db.session.commit()

            leaderboard_user = Leaderboard.query.order_by(desc(Leaderboard.coins)).limit(5).all()
            for u in leaderboard_user:
                current_leaderboard.append((u.name, u.coins))
            return jsonify(userid=user.id, leaderboard=current_leaderboard)


@app.route('/similarity_texts', methods=['POST', "GET"])
def usenet():
    if request.method == "POST":
        text1 = request.form.get("text1")
        text2 = request.form.get("text2")

        embs = get_2_embeddings(text1, text2)
        emb1 = embs[0]
        emb2 = embs[1]
        cos_similarity = cosine_similarity(emb1, emb2)

        print(text1, text2)

        return jsonify(cos_sim=cos_similarity)
    else:
        text1 = request.args.get('text1')
        text2 = request.args.get('text2')

        return jsonify(text1)


@app.route('/get_title', methods=['POST', "GET"])
def get_title():
    if request.method == "POST":
        url = request.form.get("url")

        result = requests.get(url)
        doc = BeautifulSoup(result.text, "html.parser")
        title = doc.title.string

        return jsonify(title=title)
    else:
        text1 = request.args.get('text1')
        text2 = request.args.get('text2')

        return jsonify(text1)


@app.route('/', methods=['GET'])
def index():
    return 'Machine Learning API'


if __name__ == '__main__':
    app.run(ssl_context='adhoc', debug=True, host='0.0.0.0')
