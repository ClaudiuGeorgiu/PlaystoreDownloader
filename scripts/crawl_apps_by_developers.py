#!/usr/bin/env python3

import os

from playstore.playstore import Playstore


def main():
    # Use the private credentials for this script.
    api = Playstore(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            os.path.pardir,
            "private_credentials.json",
        )
    )

    # This list has to contain the exact developer(s) name(s).
    developer_list = ["Spotify AB", "WhatsApp LLC", "Mozilla"]

    for developer in developer_list:
        for package_name in api.list_app_by_developer(developer):
            # Print package name and developer name.
            print(f"{package_name}|{developer}")


if __name__ == "__main__":
    # Run the script from the main directory of the project by using this command:
    # pipenv run python -m scripts.crawl_apps_by_developers
    main()
