#!/usr/bin/env python
# coding: utf-8

import os
import sys

from playstore.playstore import Playstore

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('Error: wrong number of parameters!')
        print("Usage: python download.py 'com.application.example'")
        sys.exit(1)

    # Make sure to use a valid json file with the credentials.
    api = Playstore('credentials.json')

    app = None

    try:
        # Get the application details.
        app = api.app_details(sys.argv[1]).docV2
    except AttributeError:
        print('Error when downloading "{0}". Unable to get app\'s details.'.format(sys.argv[1]))
        sys.exit(1)

    details = {
        'package_name': app.docid,
        'title': app.title,
        'creator': app.creator
    }

    download_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Downloads')

    # The downloaded apk will be saved in the Downloads folder
    # (created in the same folder as this script).
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    success = api.download(details['package_name'], os.path.join(download_folder,
                           '{0} by {1} - {2}.apk'.format(details['title'],
                                                         details['creator'], details['package_name'])))

    if not success:
        print('Error when downloading "{0}".'.format(details['package_name']))
