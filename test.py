import requests
import json
import time
from pymongo import Connection

SERVER_URL = 'http://localhost:9910'

db = Connection()["fueltoforest"]
db.drop_collection('users')
db.drop_collection('rides')
db.drop_collection('ride_routes')


def post(url, data, status_code=200, **kwargs):
    c =  requests.post(SERVER_URL + url, data=json.dumps(data), headers = {'content-type': 'application/json'}, **kwargs)
    assert c.status_code == status_code
    return c

post('/register', {
        'user_name': 'ybrs',
        'password': 'foobar',
        'email': 'aybars.badur@gmail.com'
    })

c = post('/login', {
    'user_name': 'ybrs',
    'password': 'foobar'
})

user = json.loads(c.content)

c = post('/rides', {
    'token': user['token'],
    'location': [29.0020, 41.0440]
}, status_code=201)

ride = json.loads(c.content)

post('/rides/%s/heartbeat' % ride['ride_id'], {
    'token': user['token'],
    'location': [29.0021, 41.0441]
}, status_code=200)

time.sleep(2)

post('/rides/%s/heartbeat' % ride['ride_id'], {
    'token': user['token'],
    'location': [29.0032, 41.0441]
}, status_code=200)

c = post('/rides/%s/finish' % ride['ride_id'], {
    'token': user['token'],
    'location': [29.3143, 41.1442]
}, status_code=200)

print c.content

