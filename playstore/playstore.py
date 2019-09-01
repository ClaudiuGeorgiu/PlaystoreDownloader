#!/usr/bin/env python
# coding: utf-8

import json
import logging
import os
import re
from typing import Iterable

import requests
from google.protobuf import json_format
from requests.exceptions import ChunkedEncodingError
from tqdm import tqdm

from playstore import playstore_proto_pb2 as playstore_protobuf
from playstore.credentials import EncryptedCredentials


class Playstore(object):

    LOGIN_URL = 'https://android.clients.google.com/auth'

    def __init__(self, config_file: str = 'credentials.json'):
        """
        Playstore object constructor.

        :param config_file: The path to the json configuration file, which contains the credentials.
        """

        self.logger = logging.getLogger('{0}.{1}'.format(__name__, self.__class__.__name__))

        # Load all the necessary configuration data and perform the login. If something goes
        # wrong in this phase, no further operations can be executed.

        try:
            self._load_configuration(config_file)

            self.android_id: str = self.configuration['ANDROID_ID']

            self.email: str = self.configuration['USERNAME']
            self.encrypted_password: bytes = EncryptedCredentials(
                self.configuration['USERNAME'], self.configuration['PASSWORD']).get_encrypted_credentials()

            self.lang_code: str = self.configuration['LANG_CODE']
            self.lang: str = self.configuration['LANG']
            self.sdk_version: str = self.configuration['SDK_VERSION']

        except json.decoder.JSONDecodeError as ex:
            self.logger.critical('The configuration file is not a valid json: {0}'.format(ex))
            raise

        except KeyError as ex:
            self.logger.critical('The configuration file is missing the {0} field'.format(ex))
            raise

        self._login()

    ##############################
    # Playstore Internal Methods #
    ##############################

    def _load_configuration(self, config_file: str) -> None:
        """
        Load the necessary configuration data contained in the specified json file.

        :param config_file: The path to the json configuration file, which contains the credentials.
        """

        if not os.path.isfile(config_file):
            self.logger.critical('Missing configuration file')
            raise FileNotFoundError('Unable to find configuration file "{0}"'.format(config_file))

        self.logger.debug('Reading {0} configuration file'.format(config_file))

        with open(config_file, 'r') as file:
            self.configuration = json.loads(file.read())[0]

    def _login(self) -> None:
        """
        Perform the login into the Play Store.

        This is needed to obtain the auth token to be used for any further requests.
        """

        params = {
            'Email': self.email,
            'EncryptedPasswd': self.encrypted_password,
            'service': 'androidmarket',
            'accountType': 'HOSTED_OR_GOOGLE',
            'has_permission': 1,
            'source': 'android',
            'device_country': self.lang,
            'lang': self.lang,
            'sdk_version': self.sdk_version
        }

        response = requests.post(self.LOGIN_URL, data=params, verify=True)

        res = {}

        for line in response.text.split():
            if '=' in line:
                tokens = line.split('=', 1)
                res[tokens[0].strip().lower()] = tokens[1].strip()

        if 'auth' in res:
            self.logger.debug('Authentication token found: {0}'.format(res['auth']))
            self.auth_token = res['auth']
        else:
            self.logger.critical('Login failed, please check your credentials')
            raise RuntimeError('Login failed, please check your credentials')

    def _execute_request(self, path: str, data: str = None) -> object:
        """
        Perform a request to the Play Store to the specified path.

        Can be used only after a successful login.

        :param path: The final part of the url to be requested (the first part
                     of the url is the same for all the requests so it's hardcoded).
        :param data: Optional body of the request.
        :return: A protobuf object containing the response to the request.
        """

        if not hasattr(self, 'auth_token'):
            self.logger.critical('Please login before attempting any other operation')
            raise RuntimeError('Please login before attempting any other operation')

        headers = {
            'Accept-Language': self.lang_code,
            'Authorization': 'GoogleLogin auth={0}'.format(self.auth_token),
            'X-DFE-Enabled-Experiments': 'cl:billing.select_add_instrument_by_default',
            'X-DFE-Unsupported-Experiments': 'nocache:billing.use_charging_poller,market_emails,'
                                             'buyer_currency,prod_baseline,checkin.set_asset_paid_app_field,'
                                             'shekel_test,content_ratings,buyer_currency_in_app,'
                                             'nocache:encrypted_apk,recent_changes',
            'X-DFE-Device-Id': self.android_id,
            'X-DFE-Client-Id': 'am-android-google',
            'User-Agent': 'Android-Finsky/4.4.3 (api=3,versionCode=8016014,sdk=23,device=hammerhead,'
                          'hardware=hammerhead,product=hammerhead)',
            'X-DFE-SmallestScreenWidthDp': '320',
            'X-DFE-Filter-Level': '3',
            'Host': 'android.clients.google.com',
        }

        if data is not None:
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

        url = 'https://android.clients.google.com/fdfe/{0}'.format(path)

        if data is not None:
            response = requests.post(url, data=data, headers=headers, verify=True)
        else:
            response = requests.get(url, headers=headers, verify=True)

        message = playstore_protobuf.ResponseWrapper.FromString(response.content)

        return message

    def _check_entire_file_downloaded(self, expected_size: int, downloaded_file_path: str) -> bool:
        """
        Check if a file was entirely downloaded.

        This works by comparing the actual size of the file with the expected size of the file.

        :param expected_size: Size (in bytes) of the file to download.
        :param downloaded_file_path: The complete path where the file has been downloaded.
        :return: True if the entire file was written to disk, False otherwise.
        """

        if expected_size != os.path.getsize(downloaded_file_path):
            self.logger.error('Download of "{0}" not completed, please retry, the file "{0}" is corrupted '
                              'and will be removed'.format(downloaded_file_path))
            try:
                os.remove(downloaded_file_path)
            except OSError:
                self.logger.warning('The file "{0}" is corrupted and should be removed manually'
                                    .format(downloaded_file_path))

            return False
        else:
            return True

    def silent_download_with_progress(self, package_name: str, file_name: str = None,
                                      download_obb: bool = False) -> Iterable[int]:
        """
        Silently download a certain app (identified by the package name) from the Google Play Store and report the
        progress (using a generator that reports the download progress in the range 0-100).

        :param package_name: The package name of the app (e.g., "com.example.myapp").
        :param file_name: The location where to save the downloaded app (by default "package_name.apk").
        :param download_obb: Flag indicating whether to also download the additional .obb files for
               an application (if any).
        :return: A generator that returns the download progress (0-100) at each iteration.
        """

        # Set the default file name if none is provided.
        if not file_name:
            file_name = '{0}.apk'.format(package_name)

        # Get the app details before downloading it.
        details = self.app_details(package_name)

        if details is None:
            self.logger.error('Can\'t proceed with the download: there was an error when '
                              'requesting details for app "{0}"'.format(package_name))
            raise RuntimeError('Can\'t proceed with the download: there was an error when '
                               'requesting details for app "{0}"'.format(package_name))

        version_code = details.docV2.details.appDetails.versionCode
        offer_type = details.docV2.offer[0].offerType

        # Check if the app was already downloaded by this account.
        path = 'delivery?ot={0}&doc={1}&vc={2}'.format(offer_type, package_name, version_code)
        response = self._execute_request(path)
        if response.payload.deliveryResponse.appDeliveryData.downloadUrl:
            # The app already belongs to the account.
            temp_url = response.payload.deliveryResponse.appDeliveryData.downloadUrl
            cookie = response.payload.deliveryResponse.appDeliveryData.downloadAuthCookie[0]
            additional_files = [additional_file for additional_file in
                                response.payload.deliveryResponse.appDeliveryData.additionalFile]
        else:
            # The app doesn't belong to the account, so it has to be added to the account.
            path = 'purchase'
            data = 'ot={0}&doc={1}&vc={2}'.format(offer_type, package_name, version_code)

            # Execute the first query to get the download link.
            response = self._execute_request(path, data)

            # If the query went completely wrong.
            if 'payload' not in self.protobuf_to_dict(response):
                try:
                    self.logger.error('Error for app "{0}": {1}'.format(package_name,
                                                                        response.commands.displayErrorMessage))
                    raise RuntimeError('Error for app "{0}": {1}'.format(package_name,
                                                                         response.commands.displayErrorMessage))
                except AttributeError:
                    self.logger.error('There was an error when requesting the download link '
                                      'for app "{0}"'.format(package_name))
                raise RuntimeError('Unable to download the application, please see the logs for more information')
            else:
                # The url where to download the apk file.
                temp_url = response.payload.buyResponse.purchaseStatusResponse.appDeliveryData.downloadUrl

                # Additional files (.obb) to be downloaded with the apk.
                additional_files = [additional_file for additional_file in
                                    response.payload.buyResponse.purchaseStatusResponse.appDeliveryData.additionalFile]

            try:
                cookie = response.payload.buyResponse.purchaseStatusResponse.appDeliveryData.downloadAuthCookie[0]
            except IndexError:
                self.logger.error('DownloadAuthCookie was not received for "{0}"'.format(package_name))
                raise RuntimeError('DownloadAuthCookie was not received for "{0}"'.format(package_name))

        cookies = {
            str(cookie.name): str(cookie.value)
        }

        headers = {
            'User-Agent': 'AndroidDownloadManager/4.1.1 (Linux; U; Android 4.1.1; Nexus S Build/JRO03E)',
            'Accept-Encoding': ''
        }

        # Execute another query to get the actual apk file.
        response = requests.get(temp_url, headers=headers, cookies=cookies, verify=True, stream=True)

        chunk_size = 1024
        apk_size = int(response.headers['content-length'])

        # Download the apk file and save it, showing a progress bar.
        try:
            with open(file_name, 'wb') as f:
                last_progress = 0
                for index, chunk in enumerate(response.iter_content(chunk_size=chunk_size)):
                    current_progress = 100 * index * chunk_size // apk_size
                    if current_progress > last_progress:
                        last_progress = current_progress
                        yield last_progress

                    if chunk:
                        f.write(chunk)
                        f.flush()

                # Download complete.
                yield 100
        except ChunkedEncodingError:
            # There was an error during the download so not all the file was written to disk, hence there will
            # be a mismatch between the expected size and the actual size of the downloaded file, but the next
            # code block will handle that.
            pass

        # Check if the entire apk was downloaded correctly, otherwise return immediately.
        if not self._check_entire_file_downloaded(apk_size, file_name):
            raise RuntimeError('Unable to download the entire application')

        if download_obb:
            # Save the additional files for the apk.
            for obb in additional_files:

                # Execute another query to get the actual file.
                response = requests.get(obb.downloadUrl, headers=headers, cookies=cookies, verify=True, stream=True)

                chunk_size = 1024
                file_size = int(response.headers['content-length'])

                obb_file_name = os.path.join(os.path.dirname(file_name),
                                             '{0}.{1}.{2}.obb'.format('main' if obb.fileType == 0 else 'patch',
                                                                      obb.versionCode, package_name))

                # Download the additional file and save it, showing a progress bar.
                try:
                    with open(obb_file_name, 'wb') as f:
                        last_progress = 0
                        for index, chunk in enumerate(response.iter_content(chunk_size=chunk_size)):
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
                    # There was an error during the download so not all the file was written to disk, hence there will
                    # be a mismatch between the expected size and the actual size of the downloaded file, but the next
                    # code block will handle that.
                    pass

                # Check if the entire additional file was downloaded correctly, otherwise return immediately.
                if not self._check_entire_file_downloaded(file_size, obb_file_name):
                    raise RuntimeError('Unable to download completely the additional files')

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
        path = 'browse?c=3'

        if category is not None:
            path += '&cat={0}'.format(requests.utils.quote(category))

        # Execute the query.
        response = self._execute_request(path)

        list_response = None

        # If the query went completely wrong.
        if 'payload' not in self.protobuf_to_dict(response):
            try:
                self.logger.error('Error when browsing categories: {0}'.format(response.commands.displayErrorMessage))
            except AttributeError:
                self.logger.error('There was an error when browsing categories')
        else:
            list_response = response.payload.browseResponse

        return list_response

    def list_app_by_category(self, category: str, subcategory: str = None, num_of_results: int = None) -> object:
        """
        Get a list of apps based on their category.

        If no subcategory is specified, the method returns a list with all the possible subcategories.

        :param category: The category to which the apps belong.
        :param subcategory: The subcategory of the apps (top free, top paid, trending etc.).
        :param num_of_results: How many results to request from the server.
        :return: A protobuf object containing the the list of apps if a valid subcategory was
                 provided, otherwise a list with the valid subcategories. The result
                 will be None if there was something wrong with the query.
        """

        # Prepare the query.
        path = 'list?c=3&cat={0}'.format(requests.utils.quote(category))

        if subcategory is not None:
            path += '&ctr={0}'.format(requests.utils.quote(subcategory))

        if num_of_results is not None:
            path += '&n={0}'.format(int(num_of_results))

        # Execute the query.
        response = self._execute_request(path)

        list_response = None

        # If the query went completely wrong.
        if 'payload' not in self.protobuf_to_dict(response):
            try:
                self.logger.error('Error when listing app by category: {0}'
                                  .format(response.commands.displayErrorMessage))
            except AttributeError:
                self.logger.error('There was an error when listing app by category')
        else:
            list_response = response.payload.listResponse

        return list_response

    # noinspection PyMethodMayBeStatic
    def list_app_by_developer(self, developer_name: str) -> list:
        """
        Get the list of apps published by a developer.

        :param developer_name: The exact name of the developer in the Google Play Store.
        :return: A list with the package names of the applications published by the specified developer.
                 An empty list will be returned if no application are found.
        """

        base_url = 'https://play.google.com/store/apps/developer?id='

        # Get the developer's page on Google Play Store.
        request_url = '{0}{1}'.format(base_url, requests.utils.quote(developer_name))
        response = requests.get(request_url, headers={
            'User-Agent': 'AndroidDownloadManager/4.1.1 (Linux; U; Android 4.1.1; Nexus S Build/JRO03E)',
        })

        # TODO: handle pagination in case there are many apps published by a developer,
        # otherwise this method will get only a subset of the total number of apps.

        # Use a regular expression to obtain the package names (the page shows only
        # applications published by the selected developer). This list might contain
        # duplicates, as the same package name can appear more than once in the page.
        package_names = re.findall(r'store/apps/details\?id=([a-zA-Z0-9._]+)', response.text)

        # Avoid duplicates.
        return list(set(package_names))

    def search(self, query: str, num_of_results: int = None) -> object:
        """
        Search for apps in the Google Play Store.

        :param query: The string describing the applications to be searched.
        :param num_of_results: How many results to request from the server.
        :return: A protobuf object containing the results of the search. The result
                 will be None if there was something wrong with the query.
        """

        # Prepare the search query.
        path = 'search?c=3&q={0}'.format(requests.utils.quote(query))

        # (Optional): set the desired number of results from the query.
        if num_of_results is not None:
            path += '&n={0}'.format(int(num_of_results))

        # Execute the search.
        response = self._execute_request(path)

        doc = None

        # If the query went completely wrong.
        if 'payload' not in self.protobuf_to_dict(response):
            try:
                self.logger.error('Error for search "{0}": {1}'.format(query, response.commands.displayErrorMessage))
            except AttributeError:
                self.logger.error('There was an error when searching for "{0}"'.format(query))
        else:
            try:
                doc = response.payload.searchResponse.doc[0]
            except IndexError:
                pass
            # If the result of the query doesn't contain the desired information.
            if not doc:
                doc = None
                self.logger.warning('There were no results when searching for "{0}", try using "{1}"'.format(
                    response.payload.searchResponse.originalQuery,
                    response.payload.searchResponse.suggestedQuery))

        return doc

    def app_details(self, package_name: str) -> object:
        """
        Get the details for a certain app (identified by the package name) in the Google Play Store.

        :param package_name: The package name of the app (e.g., "com.example.myapp").
        :return: A protobuf object containing the details of the app. The result
                 will be None if there was something wrong with the query.
        """

        # Prepare the query.
        path = 'details?doc={0}'.format(requests.utils.quote(package_name))

        # Execute the query.
        response = self._execute_request(path)

        details = None

        # If the query went completely wrong.
        if 'payload' not in self.protobuf_to_dict(response):
            try:
                self.logger.error('Error for app "{0}": {1}'.format(package_name,
                                                                    response.commands.displayErrorMessage))
            except AttributeError:
                self.logger.error('There was an error when requesting details for app "{0}"'.format(package_name))
        else:
            details = response.payload.detailsResponse

        return details

    def download(self, package_name: str, file_name: str = None, download_obb: bool = False) -> bool:
        """
        Download a certain app (identified by the package name) from the Google Play Store.

        :param package_name: The package name of the app (e.g., "com.example.myapp").
        :param file_name: The location where to save the downloaded app (by default "package_name.apk").
        :param download_obb: Flag indicating whether to also download the additional .obb files for
               an application (if any).
        :return: True if the file was downloaded correctly, False otherwise.
        """

        # Set the default file name if none is provided.
        if not file_name:
            file_name = '{0}.apk'.format(package_name)

        # Get the app details before downloading it.
        details = self.app_details(package_name)

        if details is None:
            self.logger.error('Can\'t proceed with the download, there was an error when '
                              'requesting details for app "{0}"'.format(package_name))
            return False

        version_code = details.docV2.details.appDetails.versionCode
        offer_type = details.docV2.offer[0].offerType

        # Check if the app was already downloaded by this account.
        path = 'delivery?ot={0}&doc={1}&vc={2}'.format(offer_type, package_name, version_code)
        response = self._execute_request(path)
        if response.payload.deliveryResponse.appDeliveryData.downloadUrl:
            # The app already belongs to the account.
            temp_url = response.payload.deliveryResponse.appDeliveryData.downloadUrl
            cookie = response.payload.deliveryResponse.appDeliveryData.downloadAuthCookie[0]
            additional_files = [additional_file for additional_file in
                                response.payload.deliveryResponse.appDeliveryData.additionalFile]
            split_apks = [split_apk for split_apk in
                          response.payload.deliveryResponse.appDeliveryData.split] if\
                          response.payload.deliveryResponse.appDeliveryData.split else None
        else:
            # The app doesn't belong to the account, so it has to be added to the account.
            path = 'purchase'
            data = 'ot={0}&doc={1}&vc={2}'.format(offer_type, package_name, version_code)

            # Execute the first query to get the download link.
            response = self._execute_request(path, data)

            # If the query went completely wrong.
            if 'payload' not in self.protobuf_to_dict(response):
                try:
                    self.logger.error('Error for app "{0}": {1}'.format(package_name,
                                                                        response.commands.displayErrorMessage))
                except AttributeError:
                    self.logger.error('There was an error when requesting the download link '
                                      'for app "{0}"'.format(package_name))
                return False
            else:
                # The url where to download the apk file.
                temp_url = response.payload.buyResponse.purchaseStatusResponse.appDeliveryData.downloadUrl

                # Additional files (.obb) to be downloaded with the apk.
                additional_files = [additional_file for additional_file in
                                    response.payload.buyResponse.purchaseStatusResponse.appDeliveryData.additionalFile]
                split_apks = [split_apk for split_apk in response.payload.deliveryResponse.appDeliveryData.split] if\
                              response.payload.deliveryResponse.appDeliveryData.split else None

            try:
                cookie = response.payload.buyResponse.purchaseStatusResponse.appDeliveryData.downloadAuthCookie[0]
            except IndexError:
                self.logger.error('DownloadAuthCookie was not received for "{0}"'.format(package_name))
                return False

        cookies = {
            str(cookie.name): str(cookie.value)
        }

        headers = {
            'User-Agent': 'AndroidDownloadManager/4.1.1 (Linux; U; Android 4.1.1; Nexus S Build/JRO03E)',
            'Accept-Encoding': ''
        }

        # Execute another query to get the actual apk file.
        response = requests.get(temp_url, headers=headers, cookies=cookies, verify=True, stream=True)

        chunk_size = 1024
        apk_size = int(response.headers['content-length'])

        # Download the apk file and save it, showing a progress bar.
        try:
            with open(file_name, 'wb') as f:
                for chunk in tqdm(response.iter_content(chunk_size=chunk_size), total=(apk_size // chunk_size),
                                  dynamic_ncols=True, unit=' KB', desc=('Downloading {0}'.format(package_name)),
                                  bar_format='{l_bar}{bar}|[{elapsed}<{remaining}, {rate_fmt}]'):
                    if chunk:
                        f.write(chunk)
                        f.flush()
        except ChunkedEncodingError:
            # There was an error during the download so not all the file was written to disk, hence there will
            # be a mismatch between the expected size and the actual size of the downloaded file, but the next
            # code block will handle that.
            pass

        # Check if the entire apk was downloaded correctly, otherwise return immediately.
        if not self._check_entire_file_downloaded(apk_size, file_name):
            return False

        if split_apks:
            # Save the split apks for the apk.
            for cfg_apk in split_apks:

                # Execute another query to get the actual file.
                response = requests.get(cfg_apk.downloadUrl, headers=headers, cookies=cookies, verify=True, stream=True)

                chunk_size = 1024
                file_size = int(response.headers['content-length'])

                cfg_apk_file_name = os.path.join(os.path.dirname(file_name),
                                             '{0}.{1}.{2}.apk'.format(cfg_apk.name, version_code, package_name))

                # Download the additional file and save it, showing a progress bar.
                try:
                    with open(cfg_apk_file_name, 'wb') as f:
                        for chunk in tqdm(response.iter_content(chunk_size=chunk_size), total=(file_size // chunk_size),
                                          dynamic_ncols=True, unit=' KB',
                                          desc=('Downloading Split APKs of {0}'.format(package_name)),
                                          bar_format='{l_bar}{bar}|[{elapsed}<{remaining}, {rate_fmt}]'):
                            if chunk:
                                f.write(chunk)
                                f.flush()
                except ChunkedEncodingError:
                    # There was an error during the download so not all the file was written to disk, hence there will
                    # be a mismatch between the expected size and the actual size of the downloaded file, but the next
                    # code block will handle that.
                    pass

                # Check if the entire additional file was downloaded correctly, otherwise return immediately.
                if not self._check_entire_file_downloaded(file_size, cfg_apk_file_name):
                    return False

        if download_obb:
            # Save the additional files for the apk.
            for obb in additional_files:

                # Execute another query to get the actual file.
                response = requests.get(obb.downloadUrl, headers=headers, cookies=cookies, verify=True, stream=True)

                chunk_size = 1024
                file_size = int(response.headers['content-length'])

                obb_file_name = os.path.join(os.path.dirname(file_name),
                                             '{0}.{1}.{2}.obb'.format('main' if obb.fileType == 0 else 'patch',
                                                                      obb.versionCode, package_name))

                # Download the additional file and save it, showing a progress bar.
                try:
                    with open(obb_file_name, 'wb') as f:
                        for chunk in tqdm(response.iter_content(chunk_size=chunk_size), total=(file_size // chunk_size),
                                          dynamic_ncols=True, unit=' KB',
                                          desc=('Downloading additional file of {0}'.format(package_name)),
                                          bar_format='{l_bar}{bar}|[{elapsed}<{remaining}, {rate_fmt}]'):
                            if chunk:
                                f.write(chunk)
                                f.flush()
                except ChunkedEncodingError:
                    # There was an error during the download so not all the file was written to disk, hence there will
                    # be a mismatch between the expected size and the actual size of the downloaded file, but the next
                    # code block will handle that.
                    pass

                # Check if the entire additional file was downloaded correctly, otherwise return immediately.
                if not self._check_entire_file_downloaded(file_size, obb_file_name):
                    return False

        # The apk and the additional files (if any) were downloaded correctly.
        return True
