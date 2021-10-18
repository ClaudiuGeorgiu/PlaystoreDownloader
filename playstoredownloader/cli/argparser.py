import argparse


def get_cmd_args():
    """
    Parse and return the cli parameters needed for the script execution.
    """
    parser = argparse.ArgumentParser(
        description="Download an application (.apk) from the Google Play Store."
    )
    parser.add_argument(
        "packages",
        type=str,
        nargs="+",
        help="A space sepparated list of one or more package names to download,"
        ' e.g., "com.spotify.music" or "com.whatsapp" "com.here.app.maps"',
    )
    parser.add_argument(
        "-b",
        "--blobs",
        dest="blobs",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Download the additional .obb files along with the application "
        "(if any)",
    )
    parser.add_argument(
        "-s",
        "--split-apks",
        dest="split_apks",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Download the additional split apks along with the application "
        "(if any)",
    )
    parser.add_argument(
        "-c",
        "--credentials",
        dest="credentials",
        type=str,
        metavar="FILE",
        default=argparse.SUPPRESS,
        help="The path to the JSON configuration file containing the store "
        'credentials. By default, a "private_credentials.json" file in the '
        'current directort will be tried, and then a "credentials.json"',
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        dest="out_dir",
        type=str,
        metavar="FILE",
        default=argparse.SUPPRESS,
        help="The path where to save the downloaded .apk file. By default the "
        "file will be saved in in the current directory",
    )
    parser.add_argument(
        "-t",
        "--tag",
        dest="tag",
        type=str,
        metavar="TAG",
        default=argparse.SUPPRESS,
        help="An optional tag prepended to the file name, e.g., "
        '"[TAG] filename.apk"',
    )
    return parser.parse_args()
