import tempfile
from playstore.playstore import Playstore

import sys
import os
import logging
import re

logger = logging.getLogger(__name__)

class PlaystoreClient():
    def __init__(self, playstore_client_configuration):
        try:
            credentials_file_path = playstore_client_configuration.get_credendials_file_path()
            self.api = Playstore(credentials_file_path.strip(" '\""))
        
        except Exception as ex:
            logger.critical(f"Error during the download: {ex}")
            sys.exit(1)

    def download(self, package_name, file_path="Downloads", tag=None, blobs=False, split_apks=False):
        try:
            details = self.get_app_details(package_name) 
            downloaded_apk_file_path = self._prepare_file_path_if_does_not_exist(file_path, details, tag)

            success = self.api.download(
                details["package_name"],
                downloaded_apk_file_path,
                download_obb=True if blobs else False,
                download_split_apks=True if split_apks else False,
            )

            if not success:
                logger.critical(f"Error when downloading '{details['package_name']}'")
                sys.exit(1)
        
        except Exception as ex:
            logger.critical(f"Error during the download: {ex}")
            sys.exit(1)
        

    def get_app_details(self, package_name):
        stripped_package_name = package_name.strip(" '\"")

        try:
            # Get the application details.
            app = self.api.app_details(stripped_package_name).docV2
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
        return details

    def _prepare_file_path_if_does_not_exist(self, file_path, details, tag):
        # The downloaded apk will be saved in the location chosen by the user.
        downloaded_apk_file_path = os.path.abspath(file_path.strip(" '\""))

        # If it doesn't already exist, create the directory where to save the
        # downloaded apk.
        if not os.path.isdir(os.path.dirname(downloaded_apk_file_path)):
            os.makedirs(os.path.dirname(downloaded_apk_file_path), exist_ok=True)

        if tag and tag.strip(" '\""):
            # If provided, prepend the specified tag to the file name.
            stripped_tag = tag.strip(" '\"")
            downloaded_apk_file_path = os.path.join(
                os.path.dirname(downloaded_apk_file_path),
                f"[{stripped_tag}] {os.path.basename(downloaded_apk_file_path)}",
            )
        return downloaded_apk_file_path  