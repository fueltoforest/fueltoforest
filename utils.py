import hashlib

from bson import json_util
from flask import Response


def sha1_string(s):
    sha1_checksum = hashlib.sha1()
    sha1_checksum.update(s)
    return sha1_checksum.hexdigest()


def force_unicode(text):
    if text is None:
        return u''

    if isinstance(text, unicode):
        return text

    try:
        text = unicode(text, 'utf-8')
    except UnicodeDecodeError:
        text = unicode(text, 'latin1')
    except TypeError:
        text = unicode(text)
    return text


def force_utf8(text):
    return str(force_unicode(text).encode('utf8'))


class InvalidUsage(Exception):
    def __init__(self, message, status_code=400, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def assert_if(condition, error_message, status_code=400):
    if not condition:
        raise InvalidUsage(error_message, status_code=status_code)


def jsonify(data):
    return Response(json_util.dumps(data),
                    mimetype='application/json')
