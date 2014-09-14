import uuid
from functools import wraps
from datetime import datetime

from flask import Flask, request, render_template, abort
from geopy import distance, Point
from bson import ObjectId
from pymongo import Connection, GEO2D

from utils import assert_if, sha1_string, force_utf8, InvalidUsage, jsonify


app = Flask(__name__)
db = Connection()["fueltoforest"]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/app')
def app_index():
    return render_template('app.html')


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    password = data.get('password')
    email = data.get('email')
    assert_if(password and len(password) >= 5 and len(password) < 20, "password len > 5 and < 20 ")
    assert_if(email and len(email) >= 3 and len(email) < 50 and '@' in email, "email needed ")

    # check unique
    assert_if(not db.users.find_one(dict(email=email)), "email not unique")

    hashed_password = sha1_string(force_utf8(password) + "users")

    token = sha1_string(str(uuid.uuid4()))

    bundle = {
        'name': name,
        'email': email,
        'password': hashed_password,
        'token': token
    }

    db.users.insert(bundle)
    return jsonify(bundle)


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password')
    email = data.get('email')
    assert_if(email, 'email needed')
    assert_if(password, 'password needed')

    hashed_password = sha1_string(force_utf8(password) + "users")

    user = db.users.find_one(dict(
        email=email,
        password=hashed_password
    ))

    assert_if(user, "email or password wrong")

    return jsonify(user)


@app.route('/authenticate', methods=['POST'])
def authenticate():
    token = request.json.get("token")

    user = db.users.find_one({"token": token})

    if not user:
        abort(401)

    return jsonify(user)


def require_user(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        try:
            token = request.json['token']
        except:
            token = request.args.get('token')

        if not token:
            token = request.headers.get("token")
        user = db.users.find_one({"token": token})
        if not user:
            abort(401)
        return fn(user, *args, **kwargs)
    return inner

@app.route("/rides", methods=['GET'])
@require_user
def get_rides(user):
    result = db.rides.find()
    return jsonify(result)

@app.route("/rides", methods=['POST'])
@require_user
def post_rides(user):
    data = request.json
    user_id = user['_id']
    location = data.get("location")
    inserted_id = db.rides.insert({
        "date_created": datetime.utcnow(),
        "user_id": user_id,
        "start_location": location,
        'status': 'started'
    })
    db.rides.ensure_index([("start_location", GEO2D)])
    response = jsonify({
        "ride_id": str(inserted_id)
    })
    response.status_code = 201
    return response


@app.route("/rides/<id>/heartbeat", methods=['POST'])
@require_user
def heartbeat(user, id):
    """
    Handles users current location
    """
    data = request.json
    user_id = user['_id']
    location = data.get("location")
    db.rides.ensure_index([("current_location", GEO2D)])
    db.ride_routes.ensure_index([("current_location", GEO2D)])

    ride = db.rides.find_one({'_id': ObjectId(id)})
    assert ride
    assert ride['user_id'] == user_id

    d = calc_ride_distance(ride_id=id)

    db.rides.update({'_id': ObjectId(id)},
                    {'$set':{'current_location': location,
                                 "distance": d['dis'],
                                'elapsed_seconds': d['t'],
                                "donate": calc_donate(kms=d['dis']),
                             'last_update': datetime.utcnow()}})

    db.ride_routes.insert({'current_location': location,
                            "distance": d['dis'],
                            'elapsed_seconds': d['t'],
                            "donate": calc_donate(kms=d['dis']),
                           'created_at': datetime.utcnow(),
                           'ride_id': id})


    response = jsonify({
        "ride_id": str(id),
        "distance": d['dis'],
        'elapsed_seconds': d['t'],
        "donate": calc_donate(kms=d['dis'])
    })

    response.status_code = 200
    return response

def calc_ride_distance(ride_id):
    locs = db.ride_routes.find({'ride_id': ride_id}).sort('created_at', -1)
    last_loc = None
    dis = 0
    t = 0
    for loc in locs:
        print "loc::::", loc
        lon, lat = loc['current_location']
        p = Point(latitude=lat, longitude=lon)
        loc['p'] = p
        if last_loc:
            print ">>>>", dis
            dis += distance.distance(last_loc['p'], p).km
            seconds = abs((loc['created_at'] - last_loc['created_at']).total_seconds())
            if seconds < 3600: # prolly he just forgot clicking stop
                t += seconds
        last_loc = loc
    return {'dis': dis, 't': t}


def calc_donate(kms):
    """
    TODO: tamamen scientific user behaviour driven calculation yapiyoruz,

    km basina 10 kurus, sonra TL ye ceviriyoruz,
    30 km ~ 3 lira yapiyor
    60 km ~ 7 lira yapiyor (exponantial olarak artiyor,
                            km arttikca bagis oranin fazlalasiyor ki araci daha az kullanmak isteyesin)
    >>> calc_donate(30)
    3.0
    >>> calc_donate(60)
    7.0
    >>> calc_donate(90)
    10.0

    """
    kms = (kms * 1.1)
    r =  (kms * 10) / 100
    if r < 1:
        return 1
    return round(r)

@app.route("/rides/<id>/finish", methods=['POST'])
@require_user
def finish_ride(user, id):
    """
    Finishes the ride
    """
    data = request.json
    user_id = user['_id']
    location = data.get("location")
    db.rides.ensure_index([("current_location", GEO2D)])
    db.ride_routes.ensure_index([("current_location", GEO2D)])

    ride = db.rides.find_one({'_id': ObjectId(id)})
    assert ride
    assert ride['user_id'] == user_id

    db.ride_routes.insert({'current_location': location, 'created_at': datetime.utcnow(),
                           'ride_id': id})
    db.rides.update({'_id': ObjectId(id)}, {'$set':{'end_location': location, 'status': 'finished'}})

    d = calc_ride_distance(ride_id=id)

    response = jsonify({
        "ride_id": str(id),
        "distance": d['dis'],
        'elapsed_seconds': d['t'],
        "donate": calc_donate(kms=d['dis'])
    })
    response.status_code = 200
    return response


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9910, debug=True)
