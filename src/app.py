import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, PlanetFavorite, PeopleFavorite

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def get_users():
    all_users = User.query.all()
    return jsonify([user.serialize() for user in all_users]), 200

@app.route('/user/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify(user.serialize()), 200

@app.route('/user', methods=['POST'])
def create_user():
    body = request.get_json()
    if not body:
        return jsonify({"msg": "Request body is missing"}), 400
    try:
        new_user = User(name=body['name'], email=body['email'], password=body['password'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.serialize()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400

@app.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"msg": "User deleted"}), 200

@app.route('/user/favorites/<int:id>', methods=['GET'])
def get_user_favorites(id):
    all_user_planet_favorites = PlanetFavorite.query.filter_by(user_id=id)
    all_user_people_favorites = PeopleFavorite.query.filter_by(user_id=id)

    
    return jsonify({
        "favorite_planets": [planet.serialize() for planet in all_user_planet_favorites],
        "favorite_people": [people.serialize() for people in all_user_people_favorites]
    }), 200

@app.route('/people', methods=['GET'])
def get_people():
    all_people = People.query.all()
    return jsonify([person.serialize() for person in all_people]), 200

@app.route('/people/<int:id>', methods=['GET'])
def get_person(id):
    person = People.query.get(id)
    if not person:
        return jsonify({"msg": "Person not found"}), 404
    return jsonify(person.serialize()), 200

@app.route('/planet', methods=['GET'])
def get_planets():
    all_planets = Planet.query.all()
    return jsonify([planet.serialize() for planet in all_planets]), 200

@app.route('/planet/<int:id>', methods=['GET'])
def get_planet(id):
    planet = Planet.query.get(id)
    if not planet:
        return jsonify({"msg": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200

@app.route('/planet/favorites', methods=['GET'])
def get_planet_favorites():
    all_planetfavorites = PlanetFavorite.query.all()
    return jsonify([planetfavorite.serialize() for planetfavorite in all_planetfavorites]), 200

@app.route('/favorite/planet', methods=['POST'])
def add_planet_favorite():
    body = request.get_json()
    if not body:
        return jsonify({"msg": "Request body is missing"}), 400
    
    planet_id = body.get('planet_id')
    user_id = body.get('user_id')

    if not planet_id or not user_id:
        return jsonify({"msg": "planet_id and user_id are required"}), 400

    try:
        favorite = PlanetFavorite(planet_id=planet_id, user_id=user_id)
        db.session.add(favorite)
        planet = Planet.query.get(planet_id)
        planet_serialize = planet.serialize()

        if planet_serialize["stars"] is None:
            planet.stars = 1
        else:
            planet.stars = planet_serialize["stars"]+1

        
        db.session.commit()
        return jsonify(favorite.serialize()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_planet_favorite(planet_id):
    favorite = PlanetFavorite.query.filter_by(planet_id=planet_id).first()
    if not favorite:
        return jsonify({"msg": "Favorite not found"}), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Favorite deleted"}), 200

@app.route('/favorite/people', methods=['POST'])
def add_people_favorite():
    body = request.get_json()
    if not body:
        return jsonify({"msg": "Request body is missing"}), 400
    
    people_id = body.get('people_id')
    user_id = body.get('user_id')

    if not people_id or not user_id:
        return jsonify({"msg": "people_id and user_id are required"}), 400

    try:
        favorite = PeopleFavorite(people_id=people_id, user_id=user_id)
        db.session.add(favorite)
        people = People.query.get(people_id)
        people_serialize = people.serialize()
        
        if people_serialize["stars"] is None:
            people.stars = 1
        else:
            people.stars = people_serialize["stars"]+1

        
        db.session.commit()
        return jsonify(favorite.serialize()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_people_favorite(people_id):
    favorite = PeopleFavorite.query.filter_by(people_id=people_id).first()
    if not favorite:
        return jsonify({"msg": "Favorite not found"}), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Favorite deleted"}), 200

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
