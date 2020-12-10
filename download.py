#!/usr/bin/env python3

import argparse
import logging
import os
import re
import sys

from PlaystoreDownloader import PlaystoreClient
from PlaystoreDownloader.PlaystoreClient import PlaystoreClientConfig

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
        playstore_client = PlaystoreClient.PlaystoreClient(PlaystoreClientConfig(args.credentials))

        file_path = args.out
        if file_path.strip(" '\"") == downloaded_apk_default_location:
            # The downloaded apk will be saved in the Downloads folder (created in the
            # same folder as this script).
            details = playstore_client.get_app_details(args.package)
            downloaded_apk_file_path = os.path.join(
                downloaded_apk_default_location,
                re.sub(
                    r"[^\w\-_.\s]",
                    "_",
                    f"{details['title']} by {details['creator']} - "
                    f"{details['package_name']}.apk",
                ),
            )   

        playstore_client.download(args.package, downloaded_apk_file_path, tag=args.tag, blobs=args.blobs, split_apks=args.split_apks)

    except Exception as ex:
        logger.critical(f"Error during the download: {ex}")
        sys.exit(1)


if __name__ == "__main__":
    main()
