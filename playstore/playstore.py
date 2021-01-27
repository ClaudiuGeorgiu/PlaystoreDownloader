#!/usr/bin/env python3

import json
import logging
import os
import platform
import re
import sys
from typing import Iterable

import requests
import requests.packages.urllib3.util.ssl_
from google.protobuf import json_format
from requests.exceptions import ChunkedEncodingError

from playstore import playstore_proto_pb2 as playstore_protobuf
from playstore.credentials import EncryptedCredentials
from playstore.util import Util

# Detect Python version and set the SSL ciphers accordingly. This is needed to avoid
# login errors with some versions of Python even if correct credentials are used. If
# you are still getting login errors, try different cipher combinations: the following
# should work on GitHub Actions runners, but they might not work on different machines.
# PlaystoreDownloader works best on Linux and Docker, and in such case no cipher
# modification should be needed.

if sys.version_info < (3, 6):
    raise RuntimeError("This version of Python is not supported anymore")
elif sys.version_info.major == 3 and sys.version_info.minor == 6:
    if platform.system() == "Windows":
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = (
            "ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:"
            "DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:!aNULL:!MD5"
        )
elif sys.version_info.major == 3 and (
    sys.version_info.minor == 7 or sys.version_info.minor == 8
):
    if platform.system() == "Windows":
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = (
            "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:ECDH+AESGCM:DH+AESGCM:"
            "ECDH+AES:DH+AES:RSA+AESGCM:RSA+AES:!DSS"
        )
elif sys.version_info.major == 3 and sys.version_info.minor == 9:
    if platform.system() == "Windows":
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = (
            "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:ECDH+AESGCM:DH+AESGCM:"
            "ECDH+AES:DH+AES:RSA+AESGCM:RSA+AES:!aNULL:!eNULL:!MD5:!DSS"
        )
else:
    raise RuntimeError("This version of Python is not supported yet")


class Playstore(object):

    LOGIN_URL = "https://android.clients.google.com/auth"

    def __init__(self, config_file: str = "credentials.json"):
        """
        Playstore object constructor.

        :param config_file: The path to the json configuration file, which contains
                            the credentials.
        """

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Load all the necessary configuration data and perform the login. If something
        # goes wrong in this phase, no further operations can be executed.

        try:
            self._load_configuration(config_file)

            self.android_id: str = self.configuration["ANDROID_ID"]

            self.email: str = self.configuration["USERNAME"]
            self.encrypted_password: bytes = EncryptedCredentials(
                self.configuration["USERNAME"], self.configuration["PASSWORD"]
            ).get_encrypted_credentials()

            self.lang_code: str = self.configuration["LANG_CODE"]
            self.lang: str = self.configuration["LANG"]

        except json.decoder.JSONDecodeError as ex:
            self.logger.critical(f"The configuration file is not a valid json: {ex}")
            raise

        except KeyError as ex:
            self.logger.critical(f"The configuration file is missing the {ex} field")
            raise

        self._login()

    ##############################
    # Playstore Internal Methods #
    ##############################

    def _load_configuration(self, config_file: str) -> None:
        """
        Load the necessary configuration data contained in the specified json file.

        :param config_file: The path to the json configuration file, which contains
                            the credentials.
        """

        if not os.path.isfile(config_file):
            self.logger.critical("Missing configuration file")
            raise FileNotFoundError(
                f"Unable to find configuration file '{config_file}'"
            )

        self.logger.debug(f"Reading '{config_file}' configuration file")

        with open(config_file, "r") as file:
            self.configuration = json.loads(file.read())[0]

    @Util.retry(exception=RuntimeError)
    def _login(self) -> None:
        """
        Perform the login into the Play Store.

        This is needed to obtain the auth token to be used for any further requests.
        """

        params = {
            "Email": self.email,
            "EncryptedPasswd": self.encrypted_password,
            "service": "androidmarket",
            "accountType": "HOSTED_OR_GOOGLE",
            "has_permission": 1,
            "source": "android",
            "device_country": self.lang,
            "lang": self.lang,
        }

        response = requests.post(self.LOGIN_URL, data=params, verify=True)

        res = {}

        for line in response.text.split():
            if "=" in line:
                tokens = line.split("=", 1)
                res[tokens[0].strip().lower()] = tokens[1].strip()

        if "auth" in res:
            self.logger.debug(f"Authentication token found: {res['auth']}")
            self.auth_token = res["auth"]
        else:
            raise RuntimeError("Login failed, please check your credentials")

    def _execute_request(
        self, path: str, query: dict = None, data: dict = None
    ) -> object:
        """
        Perform a request to the Play Store to the specified path.

        Can be used only after a successful login.

        :param path: The final part of the url to be requested (the first part
                     of the url is the same for all the requests so it's hardcoded).
        :param query: Optional query parameters to be used during the request.
        :param data: Optional body of the request.
        :return: A protobuf object containing the response to the request.
        """

        if not hasattr(self, "auth_token"):
            self.logger.critical("Please login before attempting any other operation")
            raise RuntimeError("Please login before attempting any other operation")

        headers = {
            "Accept-Language": self.lang_code,
            "Authorization": f"GoogleLogin auth={self.auth_token}",
            "X-DFE-Enabled-Experiments": "cl:billing.select_add_instrument_by_default",
            "X-DFE-Unsupported-Experiments": "nocache:billing.use_charging_poller,"
            "market_emails,buyer_currency,prod_baseline,"
            "checkin.set_asset_paid_app_field,shekel_test,content_ratings,"
            "buyer_currency_in_app,nocache:encrypted_apk,recent_changes",
            "X-DFE-Device-Id": self.android_id,
            "X-DFE-Client-Id": "am-android-google",
            "User-Agent": "Android-Finsky/8.5.39 (api=3,versionCode=80853900,sdk=26,"
            "device=crackling,hardware=qcom,product=crackling)",
            "X-DFE-SmallestScreenWidthDp": "320",
            "X-DFE-Filter-Level": "3",
            "Host": "android.clients.google.com",
        }

        url = f"https://android.clients.google.com/fdfe/{path}"

        if data is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
            response = requests.post(
                url, headers=headers, params=query, data=data, verify=True
            )
        else:
            response = requests.get(url, headers=headers, params=query, verify=True)

        message = playstore_protobuf.ResponseWrapper.FromString(response.content)

        return message

    def _download_single_file(
        self,
        destination_file: str,
        server_response: requests.Response,
        show_progress_bar: bool = False,
        download_str: str = "Downloading file",
        error_str: str = "Unable to download the entire file",
    ) -> Iterable[int]:
        """
        Internal method to download a file contained in a server response and save it
        to a specific destination.

        :param destination_file: The destination path where to save the downloaded file.
        :param server_response: The response from the server, containing the content of
                                the file to be saved.
        :param show_progress_bar: Flag indicating whether to show a progress bar in the
                                  terminal during the download of the file.
        :param download_str: The message to show next to the progress bar during the
                             download of the file
        :param error_str: The error message of the exception that will be raised if
                          the download of the file fails.
        :return: A generator that returns the download progress (0-100) at each
                 iteration.
        """
        chunk_size = 1024
        file_size = int(server_response.headers["Content-Length"])

        # Download the file and save it, yielding the progress (in the range 0-100).
        try:
            with open(destination_file, "wb") as f:
                last_progress = 0
                for index, chunk in enumerate(
                    Util.show_list_progress(
                        server_response.iter_content(chunk_size=chunk_size),
                        interactive=show_progress_bar,
                        unit=" KB",
                        total=(file_size // chunk_size),
                        description=download_str,
                    )
                ):
                    current_progress = 100 * index * chunk_size // file_size
                    if current_progress > last_progress:
                        last_progress = current_progress
                        yield last_progress

                    if chunk:
                        f.write(chunk)
                        f.flush()

                # Download complete.
                yield 100
        except ChunkedEncodingError:
            # There was an error during the download so not all the file was written
            # to disk, hence there will be a mismatch between the expected size and
            # the actual size of the downloaded file, but the next code block will
            # handle that.
            pass

        # Check if the entire file was downloaded correctly, otherwise raise an
        # exception.
        if file_size != os.path.getsize(destination_file):
            self.logger.error(
                f"Download of '{destination_file}' not completed, please retry, "
                f"the file '{destination_file}' is corrupted and will be removed"
            )

            try:
                os.remove(destination_file)
            except OSError:
                self.logger.warning(
                    f"The file '{destination_file}' is corrupted and should be "
                    f"removed manually"
                )

            raise RuntimeError(error_str)

    def _download_with_progress(
        self,
        package_name: str,
        file_name: str = None,
        download_obb: bool = False,
        download_split_apks: bool = False,
        show_progress_bar: bool = False,
    ) -> Iterable[int]:
        """
        Internal method to download a certain app (identified by the package name) from
        the Google Play Store and report the progress (using a generator that reports
        the download progress in the range 0-100).

        :param package_name: The package name of the app (e.g., "com.example.myapp").
        :param file_name: The location where to save the downloaded app (by default
                          "package_name.apk").
        :param download_obb: Flag indicating whether to also download the additional
                             .obb files for an application (if any).
        :param download_split_apks: Flag indicating whether to also download the
                                    additional split apks for an application (if any).
        :param show_progress_bar: Flag indicating whether to show a progress bar in the
                                  terminal during the download of the file(s).
        :return: A generator that returns the download progress (0-100) at each
                 iteration.
        """

        def _handle_missing_payload(res, pkg):
            # If the query went completely wrong.
            if "payload" not in self.protobuf_to_dict(res):
                try:
                    self.logger.error(
                        f"Error for app '{pkg}': " f"{res.commands.displayErrorMessage}"
                    )
                    raise RuntimeError(
                        f"Error for app '{pkg}': " f"{res.commands.displayErrorMessage}"
                    )
                except AttributeError:
                    self.logger.error(
                        "There was an error when requesting the download link "
                        f"for app '{pkg}'"
                    )

                raise RuntimeError(
                    "Unable to download the application, please see the logs for more "
                    "information"
                )

        # Set the default file name if none is provided.
        if not file_name:
            file_name = f"{package_name}.apk"

        # Get the app details before downloading it.
        details = self.app_details(package_name)

        if details is None:
            self.logger.error(
                "Can't proceed with the download: there was an error when "
                f"requesting details for app '{package_name}'"
            )
            raise RuntimeError(
                "Can't proceed with the download: there was an error when "
                f"requesting details for app '{package_name}'"
            )

        version_code = details.docV2.details.appDetails.versionCode
        offer_type = details.docV2.offer[0].offerType

        # Check if the app was already downloaded by this account.
        path = "delivery"
        query = {"ot": offer_type, "doc": package_name, "vc": version_code}

        response = self._execute_request(path, query)
        _handle_missing_payload(response, package_name)
        delivery_data = response.payload.deliveryResponse.appDeliveryData

        if not delivery_data.downloadUrl:
            # The app doesn't belong to the account, so it has to be added to the
            # account first.
            path = "purchase"

            response = self._execute_request(path, data=query)
            _handle_missing_payload(response, package_name)
            delivery_data = (
                response.payload.buyResponse.purchaseStatusResponse.appDeliveryData
            )
            download_token = response.payload.buyResponse.downloadToken

            if not self.protobuf_to_dict(delivery_data) and download_token:
                path = "delivery"
                query["dtok"] = download_token
                response = self._execute_request(path, query)
                _handle_missing_payload(response, package_name)
                delivery_data = response.payload.deliveryResponse.appDeliveryData

        # The url where to download the apk file.
        temp_url = delivery_data.downloadUrl

        # Additional files (.obb) to be downloaded with the application.
        # https://developer.android.com/google/play/expansion-files
        additional_files = [
            additional_file for additional_file in delivery_data.additionalFile
        ]

        # Additional split apk(s) to be downloaded with the application.
        # https://developer.android.com/guide/app-bundle/dynamic-delivery
        split_apks = [split_apk for split_apk in delivery_data.split]

        try:
            cookie = delivery_data.downloadAuthCookie[0]
        except IndexError:
            self.logger.error(
                f"DownloadAuthCookie was not received for '{package_name}'"
            )
            raise RuntimeError(
                f"DownloadAuthCookie was not received for '{package_name}'"
            )

        cookies = {str(cookie.name): str(cookie.value)}

        headers = {
            "User-Agent": "AndroidDownloadManager/8.0.0 (Linux; U; Android 8.0.0; "
            "STF-L09 Build/HUAWEISTF-L09)",
            "Accept-Encoding": "",
        }

        # Execute another request to get the actual apk file.
        response = requests.get(
            temp_url, headers=headers, cookies=cookies, verify=True, stream=True
        )

        yield from self._download_single_file(
            file_name,
            response,
            show_progress_bar,
            f"Downloading {package_name}",
            "Unable to download the entire application",
        )

        if download_obb:
            # Save the additional .obb files for this application.
            for obb in additional_files:

                # Execute another query to get the actual file.
                response = requests.get(
                    obb.downloadUrl,
                    headers=headers,
                    cookies=cookies,
                    verify=True,
                    stream=True,
                )

                obb_file_name = os.path.join(
                    os.path.dirname(file_name),
                    f"{'main' if obb.fileType == 0 else 'patch'}."
                    f"{obb.versionCode}.{package_name}.obb",
                )

                yield from self._download_single_file(
                    obb_file_name,
                    response,
                    show_progress_bar,
                    f"Downloading additional .obb file for {package_name}",
                    "Unable to download completely the additional .obb file(s)",
                )

        if download_split_apks:
            # Save the split apk(s) for this application.
            for split_apk in split_apks:

                # Execute another query to get the actual file.
                response = requests.get(
                    split_apk.downloadUrl,
                    headers=headers,
                    cookies=cookies,
                    verify=True,
                    stream=True,
                )

                split_apk_file_name = os.path.join(
                    os.path.dirname(file_name),
                    f"{split_apk.name}.{version_code}.{package_name}.apk",
                )

                yield from self._download_single_file(
                    split_apk_file_name,
                    response,
                    show_progress_bar,
                    f"Downloading split apk for {package_name}",
                    "Unable to download completely the additional split apk file(s)",
                )

    ############################
    # Playstore Public Methods #
    ############################

    @classmethod
    def protobuf_to_dict(cls, proto_obj: object) -> dict:
        """
        Convert a protobuf object into a Python dictionary.

        :param proto_obj: The protobuf object to be converted.
        :return: A Python dictionary representing the protobuf object.
        """
        return json.loads(json_format.MessageToJson(proto_obj))

    def get_store_categories(self, category: str = None) -> object:
        """
        Get the names of the categories of apps in the Google Play Store.

        :param category: If a valid category is specified, this method will return
                         its subcategories (if any).
        :return: A protobuf object containing the list of categories. The result
                 will be None if there was something wrong with the query.
        """

        # Prepare the query.
        path = "browse"
        query = {"c": 3}

        if category is not None:
            query["cat"] = requests.utils.quote(category)

        # Execute the query.
        response = self._execute_request(path, query)

        list_response = None

        # If the query went completely wrong.
        if "payload" not in self.protobuf_to_dict(response):
            try:
                self.logger.error(
                    "Error when browsing categories: "
                    f"{response.commands.displayErrorMessage}"
                )
            except AttributeError:
                self.logger.error("There was an error when browsing categories")
        else:
            list_response = response.payload.browseResponse

        return list_response

    def list_app_by_category(
        self, category: str, subcategory: str = None, num_of_results: int = None
    ) -> object:
        """
        Get a list of apps based on their category.

        If no subcategory is specified, the method returns a list with all the
        possible subcategories.

        :param category: The category to which the apps belong.
        :param subcategory: The subcategory of the apps (top free, top paid,
                            trending etc.).
        :param num_of_results: How many results to request from the server.
        :return: A protobuf object containing the the list of apps if a valid
                 subcategory was provided, otherwise a list of strings with the
                 valid subcategories. The result will be None if there was
                 something wrong with the query.
        """

        # Prepare the query.
        path = "list"
        query = {"c": 3, "cat": requests.utils.quote(category)}

        if subcategory is not None:
            query["ctr"] = requests.utils.quote(subcategory)

        if num_of_results is not None:
            query["n"] = int(num_of_results)

        # Execute the query.
        response = self._execute_request(path, query)

        list_response = None

        # If the query went completely wrong.
        if "payload" not in self.protobuf_to_dict(response):
            try:
                self.logger.error(
                    "Error when listing app by category: "
                    f"{response.commands.displayErrorMessage}"
                )
            except AttributeError:
                self.logger.error("There was an error when listing app by category")
        else:
            if subcategory is not None:
                list_response = response.payload.listResponse
            else:
                list_response = []
                for pre_fetch in response.preFetch:
                    for doc in pre_fetch.response.payload.listResponse.doc:
                        list_response.append(doc.docid or doc.child[0].docid)

        return list_response or None

    # noinspection PyMethodMayBeStatic
    def list_app_by_developer(self, developer_name: str) -> list:
        """
        Get the list of apps published by a developer.

        :param developer_name: The exact name of the developer in the Google Play Store.
        :return: A list with the package names of the applications published by the
                 specified developer. An empty list will be returned if no application
                 are found.
        """

        base_url = "https://play.google.com/store/apps/developer?id="

        # Get the developer's page on Google Play Store.
        request_url = f"{base_url}{requests.utils.quote(developer_name)}"
        response = requests.get(
            request_url,
            headers={
                "User-Agent": "AndroidDownloadManager/8.0.0 (Linux; U; Android 8.0.0; "
                "STF-L09 Build/HUAWEISTF-L09)",
            },
        )

        # TODO: handle pagination in case there are many apps published by a developer,
        #  otherwise this method will get only a subset of the total number of apps.

        # Use a regular expression to obtain the package names (the page shows only
        # applications published by the selected developer). This list might contain
        # duplicates, as the same package name can appear more than once in the page.
        package_names = re.findall(
            r"store/apps/details\?id=([a-zA-Z0-9._]+)", response.text
        )

        # Avoid duplicates.
        return list(set(package_names))

    def search(self, query: str) -> object:
        """
        Search for apps in the Google Play Store.

        :param query: The string describing the applications to be searched.
        :return: A protobuf object containing the results of the search. The result
                 will be None if there was something wrong with the query.
        """

        # Prepare the search query.
        path = "search"
        query = {"c": 3, "q": requests.utils.quote(query)}

        # Execute the search.
        response = self._execute_request(path, query)

        doc = None

        # If the query went completely wrong.
        if "payload" not in self.protobuf_to_dict(response):
            try:
                self.logger.error(
                    f"Error for search '{query}': "
                    f"{response.commands.displayErrorMessage}"
                )
            except AttributeError:
                self.logger.error(f"There was an error when searching for '{query}'")
        else:
            try:
                doc = response.payload.searchResponse.doc[0]
            except IndexError:
                try:
                    doc = (
                        response.preFetch[0]
                        .response.payload.listResponse.doc[0]
                        .child[0]
                    )
                except IndexError:
                    pass
            # If the result of the query doesn't contain the desired information.
            if not doc:
                doc = None
                self.logger.warning(
                    "There were no results when searching for "
                    f"'{response.payload.searchResponse.originalQuery}', "
                    f"try using '{response.payload.searchResponse.suggestedQuery}'"
                )

        return doc

    def app_details(self, package_name: str) -> object:
        """
        Get the details for a certain app (identified by the package name) in the
        Google Play Store.

        :param package_name: The package name of the app (e.g., "com.example.myapp").
        :return: A protobuf object containing the details of the app. The result
                 will be None if there was something wrong with the query.
        """

        # Prepare the query.
        path = "details"
        query = {"doc": requests.utils.quote(package_name)}

        # Execute the query.
        response = self._execute_request(path, query)

        details = None

        # If the query went completely wrong.
        if "payload" not in self.protobuf_to_dict(response):
            try:
                self.logger.error(
                    f"Error for app '{package_name}': "
                    f"{response.commands.displayErrorMessage}"
                )
            except AttributeError:
                self.logger.error(
                    f"There was an error when requesting details for "
                    f"app '{package_name}'"
                )
        else:
            details = response.payload.detailsResponse

        return details

    def download(
        self,
        package_name: str,
        file_name: str = None,
        download_obb: bool = False,
        download_split_apks: bool = False,
        show_progress_bar: bool = True,
    ) -> bool:
        """
        Download a certain app (identified by the package name) from the
        Google Play Store.

        :param package_name: The package name of the app (e.g., "com.example.myapp").
        :param file_name: The location where to save the downloaded app (by default
                          "package_name.apk").
        :param download_obb: Flag indicating whether to also download the additional
                             .obb files for an application (if any).
        :param download_split_apks: Flag indicating whether to also download the
                                    additional split apks for an application (if any).
        :param show_progress_bar: Flag indicating whether to show a progress bar in the
                                  terminal during the download of the file(s).
        :return: True if the file was downloaded correctly, False otherwise.
        """

        try:
            # Consume the generator reporting the download progress.
            list(
                self._download_with_progress(
                    package_name,
                    file_name,
                    download_obb,
                    download_split_apks,
                    show_progress_bar,
                )
            )
        except Exception as e:
            self.logger.error(f"Error during the download: {e}", exc_info=True)
            return False

        # The apk and the additional files (if any) were downloaded correctly.
        return True
