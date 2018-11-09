#!/usr/bin/env python
# coding: utf-8

# The following 2 lines have to stay at the top of the file!
import eventlet
eventlet.monkey_patch()

import logging
import os
import re

from flask import Flask, make_response, jsonify
from flask import render_template
from flask_socketio import SocketIO, emit

from playstore.playstore import Playstore

if 'LOG_LEVEL' in os.environ:
    log_level = os.environ['LOG_LEVEL']
else:
    log_level = logging.INFO

# Logging configuration.
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s> [%(levelname)s][%(name)s][%(funcName)s()] %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S', level=log_level)

# Credentials file location (make sure to use a valid json file with the credentials).
credentials_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'private_credentials.json')

# Directory where to save the downloaded applications.
downloaded_apk_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Downloads')

# https://developer.android.com/guide/topics/manifest/manifest-element#package
package_name_regex = re.compile('^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$', flags=re.IGNORECASE)


def create_app():
    app = Flask(__name__)
    # Create the upload directory (if not already existing).
    if not os.path.isdir(downloaded_apk_location):
        os.makedirs(downloaded_apk_location)
    return app


application = create_app()
socket = SocketIO(application, ping_timeout=600)


@application.after_request
def add_cache_header(response):
    response.headers['Cache-Control'] = 'public, max-age=0, no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@application.errorhandler(400)
@application.errorhandler(500)
def application_error(error):
    logger.error(error)
    return make_response(jsonify(str(error)), error.code)


@application.route('/', methods=['GET'], strict_slashes=False)
def home():
    return render_template('index.html')


@socket.on('start_download')
def on_start_download(package_name):
    if package_name_regex.match(package_name):
        try:
            api = Playstore(credentials_location)
            try:
                app = api.app_details(package_name).docV2
            except AttributeError:
                emit('download_bad_package',
                     'Unable to retrieve application with package name "{0}".'.format(package_name))
                return

            details = {
                'package_name': app.docid,
                'title': app.title,
                'creator': app.creator
            }
            downloaded_apk_file_path = os.path.join(
                downloaded_apk_location,
                re.sub(r'[^\w\-_.\s]', '_', '{0} by {1} - {2}.apk'.format(details['title'],
                                                                          details['creator'],
                                                                          details['package_name'])))

            for progress in api.silent_download_with_progress(details['package_name'], downloaded_apk_file_path):
                emit('download_progress', progress)

            logger.info('The application was downloaded and saved to "{0}".'.format(downloaded_apk_file_path))
            emit('download_success', 'The application was successfully downloaded.')
        except Exception as e:
            emit('download_error', str(e))
    else:
        emit('download_error', 'Please specify a valid package name.')


if __name__ == '__main__':
    socket.run(application, host='0.0.0.0', port=5000)
