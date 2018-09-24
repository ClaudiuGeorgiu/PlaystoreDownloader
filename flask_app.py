import json
import logging
import os
import re
import time
import threading

from download import flask_direct_download
from flask import Flask, make_response, jsonify
from flask import render_template
from flask import request
from werkzeug.exceptions import BadRequest, UnprocessableEntity, InternalServerError
from werkzeug.utils import secure_filename


DDIR = 'DOWNLOAD_DIR'

if 'LOG_LEVEL' in os.environ:
    log_level = os.environ['LOG_LEVEL']
else:
    log_level = logging.DEBUG

# Logging configuration.
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s> [%(levelname)s][%(name)s][%(funcName)s()] %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S', level=log_level)

def create_app():
    app = Flask(__name__)
    app.config[DDIR] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Downloads')
    # Create the upload directory (if not already existing).
    if not os.path.exists(app.config[DDIR]):
        os.makedirs(app.config[DDIR])
    return app


application = create_app()


@application.errorhandler(400)
@application.errorhandler(422)
@application.errorhandler(500)
def application_error(error):
    logger.error(error)
    return make_response(jsonify(str(error)), error.code)


@application.route('/', methods=['GET'], strict_slashes=False)
def home():
    return render_template('index.html')


class GPlayDownloaderThread(threading.Thread):
    def __init__(self, package_name):
        self.package_name = package_name
        super().__init__()

    def run(self):
        flask_direct_download(self.package_name)


pack_name_regex = re.compile('^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+[0-9a-z_]$', flags=re.IGNORECASE)


@application.route('/download_apk', methods=['POST'], strict_slashes=False)
def download_apk():
    if request.method == 'POST':
        result = request.form
        if 'packagename' in result:
            package_name = result['packagename']
            if pack_name_regex.match(package_name):
                GPlayDownloaderThread(package_name).start()
                return render_template('success.html', packname=package_name)
    return render_template('index.html')


if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000)
