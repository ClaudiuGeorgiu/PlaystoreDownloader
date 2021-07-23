import argparse
from pathlib import Path

# Default directory where to save the downloaded applications.

# Default credentials file location.
credentials_default_location = Path.cwd() / "credentials.json"

def get_cmd_args():
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
    return parser.parse_args()
