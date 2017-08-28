#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import re
import sys

from playstore.playstore import Playstore


def main():

    downloaded_apk_default_location = 'Downloads'

    parser = argparse.ArgumentParser(description='Download an application (.apk) from the Google Play Store.')
    parser.add_argument('package', nargs=1, type=str, help='The package name of the application to be downloaded, '
                                                           'e.g. "com.spotify.music" or "com.whatsapp"')
    parser.add_argument('-o', '--out', type=str, metavar='FILE', default=downloaded_apk_default_location,
                        help='The path where to save the downloaded .apk file. By default the file will be saved '
                             'in a "Downloads/" directory created where this script is run')
    args = parser.parse_args()

    # Make sure to use a valid json file with the credentials.
    api = Playstore('credentials.json')

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

    if args.out == downloaded_apk_default_location:
        # The downloaded apk will be saved in the Downloads folder (created in the same folder as this script).
        downloaded_apk_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                downloaded_apk_default_location,
                                                re.sub('[^\w\-_.\s]', '_', '{0} by {1} - {2}.apk'
                                                       .format(details['title'], details['creator'],
                                                               details['package_name'])))
    else:
        # The downloaded apk will be saved in the location chosen by the user.
        downloaded_apk_file_path = os.path.abspath(args.out)

    # If it doesn't exist, create the directory where to save the downloaded apk.
    if not os.path.exists(os.path.dirname(downloaded_apk_file_path)):
        os.makedirs(os.path.dirname(downloaded_apk_file_path))

    success = api.download(details['package_name'], downloaded_apk_file_path)

    if not success:
        print('Error when downloading "{0}".'.format(details['package_name']))


if __name__ == '__main__':
    main()
