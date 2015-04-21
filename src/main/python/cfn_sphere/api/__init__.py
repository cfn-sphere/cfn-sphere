import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, Response, render_template
from flask_restful import Api
from cfn_sphere.api.resource.stack import Stack


app = Flask(__name__)
api = Api(app)

app.secret_key = os.urandom(24)

# api resources
api.add_resource(Stack, '/stacks/<string:stack_id>')


def render_application_template(template_name, **template_parameters):
    return render_template(template_name, **template_parameters)


def init_access_log(access_log_file):
    logger = logging.getLogger('werkzeug')
    handler = RotatingFileHandler(access_log_file, maxBytes=10000, backupCount=5)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def run(bind, port, debug, access_log_file=False):
    if access_log_file:
        init_access_log(access_log_file)
    app.run(bind, port, threaded=True, debug=debug)


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    version = '1.0'
    return render_application_template('index.html', **locals())


if __name__ == '__main__':
    run(bind='127.0.0.1', port=8080, debug=True)