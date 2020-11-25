import tempfile
from playstore.playstore import Playstore

class PlaystoreClient():
    def __init__(self, credentials_file_path="credentials.json"):
        try:
            self.api = Playstore(credentials_file_path.strip(" '\""))
        
        except Exception as ex:
            logger.critical(f"Error during the download: {ex}")
            sys.exit(1)

    def download(self, package_name, file_path="Downloads", tag=None, blobs=False, split_apks=False):
        try:
            details = self._get_app_details(package_name)
            downloaded_apk_file_path = self._prepare_file_path(file_path, tag)

            success = api.download(
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
        

    def _get_app_details(self, package_name):
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

    def _prepare_file_path(self, file_path, tag):
        if file_path.strip(" '\"") == downloaded_apk_default_location:
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


class PlaystoreClientCredentials(PlaystoreClient):
    def __init__(self, username, password, android_id, lang_code='en_US', lang='us'):
        try:
            credentials_json_struct = [
            {
                "USERNAME": username,
                "PASSWORD": password,
                "ANDROID_ID": android_id,
                "LANG_CODE": "en_US",
                "LANG": "us"
            }
            ]
            
            self.credentials_file = tempfile.NamedTemporaryFile(delete=False)
            json.dump(credentials_json_struct, self.credentials_file)

            super.__init__(self.credentials_file.name)
        
        except Exception as ex:
            logger.critical(f"Error during the download: {ex}")
            sys.exit(1)

    def download(self, package_name, file_path="Downloads", tag=None, blobs=False, split_apks=False):
        super().download(package_name, file_path=file_path, tag=tag, blobs=blobs, split_apks=split_apks)

    def __del__(self):
        self.credentials_file.close()    