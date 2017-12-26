import os
import uuid
from functools import wraps
from pprint import pprint

import requests
from redis import Redis

from flask import Flask, jsonify, request

api = Flask(__name__)

host = os.getenv('REDIS_HOST', 'localhost')
redis = Redis(host=host, port=6379)

# Env settings
ADMIN_API_KEY = os.getenv('ADMIN_API_KEY')
FORWARD_HOST = os.getenv('FORWARD_HOST')
FORWARD_PORT = os.getenv('FORWARD_PORT', 80)
FULL_URL = "%s:%s" % (FORWARD_HOST, FORWARD_PORT)
CHECK_HEADER = os.getenv('CHECK_HEADER', 'api-key')
CHECK_QUERY = os.getenv('CHECK_QUERY')
DEBUG = os.getenv('DEBUG')

# Routes
LS_API_KEY = "/%s/ls/<key>" % ADMIN_API_KEY
RM_API_KEY = "/%s/rm/<key>" % ADMIN_API_KEY
ADD_API_KEY = "/%s/add/<total>" % ADMIN_API_KEY
ADD_API_KEY_SPECIFIC = "/%s/add/<total>/<key>" % ADMIN_API_KEY
ROUTES_DESCIPTION = {
    LS_API_KEY: 'Describe the usage for <key>',
    RM_API_KEY: 'Remove the api key <key>',
    ADD_API_KEY: 'Generate a API key with <total>. Key is returned..',
    ADD_API_KEY_SPECIFIC: 'Register an API Key <key> with usage <total>',
}

# Errors
SERVER_FAILED = {'error': 'An unknown error occured.', 'type': 'ServerCrashed'}

NO_API_KEY_ERROR = {
    'error':
    'No API Key Provided. Please add the \'%s\' header' % CHECK_HEADER,
    'type': 'NoApiKeyGiven',
}

FAILED_ADMIN_AUTH_ERROR = {
    'error': 'You must be an Admin to access this resource',
    'type': 'FailedAdminAuth'
}

KEY_DOES_NOT_EXIST = {'error': 'Key Does not Exist'}

API_KEY_NOT_FOUND = {
    'error': 'You are not authenticated. Please check your API Key.',
    'type': 'AuthFailed'
}

RATE_EXCEEDED = {
    'error': 'Rate Exceeded. Please contact us to increase your limit',
    'type': 'RateExceeded'
}


def success(msg='success', extra={}):
    return jsonify({'message': msg, **extra})


def auth_failed(details, extra={}):
    return jsonify({**details, **extra}), 403


def not_found(details):
    return jsonify(details), 404


MESSAGE_SUCCESS = {'message': 'success'}


class AuthFailed(Exception):
    pass


def auth(some_function):
    @wraps(some_function)
    def check_auth(*args, **kwargs):
        try:
            api_key = request.headers.get(CHECK_HEADER)
            if api_key is None and CHECK_QUERY:
                api_key = request.args.get(CHECK_QUERY)
            if api_key is None:
                return auth_failed(NO_API_KEY_ERROR)
            if api_key == ADMIN_API_KEY:
                return some_function(*args, **kwargs)
            api_usage = redis.get(api_key)
            if api_usage is None:
                return auth_failed(API_KEY_NOT_FOUND)
            if int(api_usage) <= 0:
                return auth_failed(RATE_EXCEEDED)
            # Decrement api_usage (key = api_key)
            redis.decr(api_key)
            return some_function(*args, **kwargs)
        except Exception as e:
            if DEBUG:
                raise e
            return jsonify(SERVER_FAILED), 500

    return check_auth


def rate_exceeded(api_key):
    usage = redis.get(api_key)
    return usage is None or int(redis.get(api_key)) <= 0


@api.route(ADD_API_KEY_SPECIFIC)
def add_api_key_specific(total, key):
    redis.set(key, total)
    return success(extra={'key': key, 'total': total})


@api.route(ADD_API_KEY)
def add_api_key(total):
    key = str(uuid.uuid4()).replace('-', '')
    redis.set(key, int(total))
    return success(extra={'key': key, 'total': total})


@api.route(RM_API_KEY)
def rm_api_key(key):
    redis.delete(key)
    return success(extra={'rm': key})


@api.route(LS_API_KEY)
def ls_api_key(key):
    total = redis.get(key)
    if total is None:
        return not_found({
            'key': key,
            'error': 'Not Found',
            'type': 'NotFound'
        })
    return success(extra={'key': key, 'ls': int(total)})


def format_url(path, query_params):
    query_params_str = ""
    for key, value in query_params.items():
        if query_params_str:
            query_params_str += '&'
        if not value:
            query_params_str += 'key'
        else:
            query_params_str += "%s=%s" % (key, value)
    url = "http://%s/%s" % (FULL_URL, path)
    if query_params_str:
        url += '?' + query_params_str
    return url


@api.route('/', defaults={'path': ''})
@api.route('/<path:path>', methods=['GET', 'POST', 'PUT'])
@auth
def proxy(path):
    headers = request.headers
    cookies = request.cookies
    query_params = request.args
    url = format_url(path, query_params)
    method = request.method
    kwargs = {
        'headers': headers,
        'cookies': cookies,
    }
    if method == 'GET':
        resp = requests.get(url, **kwargs)
    elif method == 'POST':
        resp = requests.post(url, data=request.data, **kwargs)
    elif method == 'PUT':
        resp = requests.put(url, data=request.data, **kwargs)
    return (resp.content, resp.status_code, resp.headers.items())


if __name__ == "__main__":
    pprint(ROUTES_DESCIPTION)
    api.run(host="0.0.0.0", port=8080)
