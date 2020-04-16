#!/usr/bin/env python3

import argparse
import logging
import os
import re
import sys

from playstore.playstore import Playstore

# Logging configuration.
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s> [%(levelname)s][%(name)s][%(funcName)s()] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    level=logging.INFO,
)

# Default credentials file location.
credentials_default_location = "credentials.json"

# Default directory where to save the downloaded applications.
downloaded_apk_default_location = "Downloads"


def get_cmd_args(args: list = None):
    """
    Parse and return the command line parameters needed for the script execution.

    :param args: Optional list of arguments to be parsed (by default sys.argv is used).
    :return: The command line needed parameters.
    """
    parser = argparse.ArgumentParser(
        description="Download an application (.apk) from the Google Play Store."
    )
    parser.add_argument(
        "package",
        type=str,
        help="The package name of the application to be downloaded, "
        'e.g., "com.spotify.music" or "com.whatsapp"',
    )
    parser.add_argument(
        "-b",
        "--blobs",
        action="store_true",
        help="Download the additional .obb files along with the application (if any)",
    )
    parser.add_argument(
        "-s",
        "--split-apks",
        action="store_true",
        help="Download the additional split apks along with the application (if any)",
    )
    parser.add_argument(
        "-c",
        "--credentials",
        type=str,
        metavar="CREDENTIALS",
        default=credentials_default_location,
        help="The path to the JSON configuration file containing the store "
        'credentials. By default a "credentials.json" file in the current directory '
        "will be used",
    )
    parser.add_argument(
        "-o",
        "--out",
        type=str,
        metavar="FILE",
        default=downloaded_apk_default_location,
        help="The path where to save the downloaded .apk file. By default the file "
        'will be saved in a "Downloads/" directory created where this script '
        "is run",
    )
    parser.add_argument(
        "-t",
        "--tag",
        type=str,
        metavar="TAG",
        help='An optional tag prepended to the file name, e.g., "[TAG] filename.apk"',
    )
    return parser.parse_args(args)


def main():

    args = get_cmd_args()

    try:

        # Make sure to use a valid json file with the credentials.
        api = Playstore(args.credentials.strip(" '\""))

        stripped_package_name = args.package.strip(" '\"")

        try:
            # Get the application details.
            app = api.app_details(stripped_package_name).docV2
        except AttributeError:
            logger.critical(
                f"Error when downloading '{stripped_package_name}': unable to "
                f"get app's details"
            )
            sys.exit(1)

        details = {
            "package_name": app.docid,
            "title": app.title,
            "creator": app.creator,
        }

        if args.out.strip(" '\"") == downloaded_apk_default_location:
            # The downloaded apk will be saved in the Downloads folder (created in the
            # same folder as this script).
            downloaded_apk_file_path = os.path.join(
                downloaded_apk_default_location,
                re.sub(
                    r"[^\w\-_.\s]",
                    "_",
                    f"{details['title']} by {details['creator']} - "
                    f"{details['package_name']}.apk",
                ),
            )
        else:
            # The downloaded apk will be saved in the location chosen by the user.
            downloaded_apk_file_path = os.path.abspath(args.out.strip(" '\""))

        # If it doesn't already exist, create the directory where to save the
        # downloaded apk.
        if not os.path.isdir(os.path.dirname(downloaded_apk_file_path)):
            os.makedirs(os.path.dirname(downloaded_apk_file_path), exist_ok=True)

        if args.tag and args.tag.strip(" '\""):
            # If provided, prepend the specified tag to the file name.
            stripped_tag = args.tag.strip(" '\"")
            downloaded_apk_file_path = os.path.join(
                os.path.dirname(downloaded_apk_file_path),
                f"[{stripped_tag}] {os.path.basename(downloaded_apk_file_path)}",
            )

        # The download of the additional files is optional.
        success = api.download(
            details["package_name"],
            downloaded_apk_file_path,
            download_obb=True if args.blobs else False,
            download_split_apks=True if args.split_apks else False,
        )

        if not success:
            logger.critical(f"Error when downloading '{details['package_name']}'")
            sys.exit(1)

    except Exception as ex:
        logger.critical(f"Error during the download: {ex}")
        sys.exit(1)


if __name__ == "__main__":
    main()
