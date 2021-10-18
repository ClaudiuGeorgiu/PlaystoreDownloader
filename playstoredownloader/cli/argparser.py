#!/usr/bin/env python3

import argparse


def get_cmd_args():
    """
    Parse and return the command line parameters needed for the script execution.

    :return: The command line needed parameters.
    """
    parser = argparse.ArgumentParser(
        prog="python3 -m playstoredownloader.cli",
        description="Download applications (.apk files) from the Google Play Store.",
    )
    parser.add_argument(
        "package",
        type=str,
        nargs="+",
        help="The package name of the application to be downloaded, "
        'e.g., "com.spotify.music" or "com.whatsapp". Can be specified multiple times '
        "as a space separated list to download more packages, e.g., "
        '"com.spotify.music" "com.whatsapp" "com.here.app.maps"',
    )
    parser.add_argument(
        "-b",
        "--blobs",
        dest="blobs",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Download the additional .obb files along with the application (if any)",
    )
    parser.add_argument(
        "-s",
        "--split-apks",
        dest="split_apks",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Download the additional split apks along with the application (if any)",
    )
    parser.add_argument(
        "-c",
        "--credentials",
        dest="credentials",
        type=str,
        metavar="FILE",
        default=argparse.SUPPRESS,
        help="The path to the JSON configuration file containing the store "
        'credentials. By default, a "credentials.json" file in the current directory '
        'will be used (if present, a "private_credentials.json" file will be used '
        "instead)",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        dest="out_dir",
        type=str,
        metavar="DIR",
        default=argparse.SUPPRESS,
        help="The path of the directory where to save the downloaded .apk file(s). By "
        'default, the file(s) will be saved in a "Downloads/" directory created '
        "in the current folder",
    )
    parser.add_argument(
        "-t",
        "--tag",
        dest="tag",
        type=str,
        metavar="TAG",
        default=argparse.SUPPRESS,
        help="An optional tag prepended to the file name of the downloaded app(s), "
        'e.g., "[TAG] filename.apk"',
    )
    return parser.parse_args()
