import argparse

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
    return vars(parser.parse_args())

def main(package):
    print(package)

main(**get_cmd_args())
