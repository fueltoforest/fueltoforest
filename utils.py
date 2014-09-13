import hashlib


def sha1_string(s):
    sha1_checksum = hashlib.sha1()
    sha1_checksum.update(s)
    return sha1_checksum.hexdigest()


def force_unicode(text):
    if text == None:
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
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def assert_if(condition, error_message):
    if not condition:
        raise InvalidUsage(error_message)
