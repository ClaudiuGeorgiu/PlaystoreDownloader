#!/usr/bin/env python
# coding: utf-8

import json
import logging
import os
import sys

import requests
from google.protobuf import json_format
from tqdm import tqdm

from . import playstore_proto_pb2 as playstore_protobuf
from .credentials import EncryptedCredentials


# Logging configuration.
logging.basicConfig(format='%(asctime)s> [%(levelname)s][%(funcName)s()] %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
logger = logging.getLogger(__name__)


class Playstore(object):

    LOGIN_URL = 'https://android.clients.google.com/auth'

    def __init__(self, config_file: str = 'credentials.json', debug: bool = False):
        """
        Playstore object constructor.
        :param config_file: The path to the json configuration file, which contains the credentials.
        :param debug: If set to True, more debug messages will be printed into the console.
        """

        if debug:
            logger.setLevel(logging.DEBUG)

        # Load all the necessary configuration data and perform the login. If something goes
        # wrong in this phase, no further operations can be executed.

        try:
            self._load_configuration(config_file)

            self.androidId = self.configuration['ANDROID_ID']

            self.email = self.configuration['USERNAME']
            self.encrypted_password = EncryptedCredentials(self.configuration['USERNAME'],
                                                           self.configuration['PASSWORD']).get_encrypted_credentials()

            self.lang_code = self.configuration['LANG_CODE']
            self.lang = self.configuration['LANG']
            self.sdk_version = self.configuration['SDK_VERSION']

        except json.decoder.JSONDecodeError as ex:
            logging.critical('The configuration file is not a valid json: {0}.'.format(ex))
            sys.exit(1)

        except KeyError as ex:
            logging.critical('The configuration file is missing the {0} field.'.format(ex))
            sys.exit(1)

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
            logging.critical('Missing configuration file.')
            sys.exit(1)

        logging.debug('Reading {0} configuration file.'.format(config_file))

        with open(config_file, 'r') as file:
            self.configuration = json.loads(file.read())[0]

    def _login(self) -> None:
        """
        Perform the login into the Play Store. This is needed to obtain the auth token to be used
        for any further requests.
        """

        params = {
            'Email': self.email,
            'EncryptedPasswd': self.encrypted_password,
            'service': 'androidmarket',
            'accountType': 'HOSTED_OR_GOOGLE',
            'has_permission': 1,
            'source': 'android',
            'androidId': self.androidId,
            'app': 'com.android.vending',
            'device_country': self.lang,
            'operatorCountry': self.lang,
            'lang': self.lang,
            'sdk_version': self.sdk_version
        }

        headers = {
            'Accept-Encoding': '',
        }

        response = requests.post(self.LOGIN_URL, data=params, headers=headers, verify=True)

        res = {}

        for line in response.text.split():
            if '=' in line:
                tokens = line.split('=', 1)
                res[tokens[0].strip().lower()] = tokens[1].strip()

        if 'auth' in res:
            logger.debug('Authentication token found: {0}.'.format(res['auth']))
            self.auth_token = res['auth']
        else:
            logging.critical('Login failed. Please check your credentials.')
            sys.exit(1)

    def _execute_request(self, path: str, data: str = None) -> object:
        """
        Perform a request to the Play Store to the specified path. Can be used
        only after a successful login.
        :param path: The final part of the url to be requested (the first part
        of the url is the same for all the requests so it's hardcoded).
        :param data: Optional body of the request.
        :return: A protobuf object containing the response to the request.
        """

        if not hasattr(self, 'auth_token'):
            logging.critical('Please login before attempting any other operation.')
            sys.exit(1)

        headers = {
            'Accept-Language': self.lang_code,
            'Authorization': 'GoogleLogin auth={0}'.format(self.auth_token),
            'X-DFE-Enabled-Experiments': 'cl:billing.select_add_instrument_by_default',
            'X-DFE-Unsupported-Experiments': 'nocache:billing.use_charging_poller,market_emails,'
                                             'buyer_currency,prod_baseline,checkin.set_asset_paid_app_field,'
                                             'shekel_test,content_ratings,buyer_currency_in_app,'
                                             'nocache:encrypted_apk,recent_changes',
            'X-DFE-Device-Id': self.androidId,
            'X-DFE-Client-Id': 'am-android-google',
            'User-Agent': 'Android-Finsky/4.4.3 (api=3,versionCode=8016014,sdk=23,device=hammerhead,'
                          'hardware=hammerhead,product=hammerhead)',
            'X-DFE-SmallestScreenWidthDp': '320',
            'X-DFE-Filter-Level': '3',
            'Accept-Encoding': '',
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
                logging.error('Error when browsing categories: {0}'.format(response.commands.displayErrorMessage))
            except AttributeError:
                logging.error('There was an error when browsing categories.')
        else:
            list_response = response.payload.browseResponse

        return list_response

    def list_app_by_category(self, category: str, subcategory: str = None, num_of_results: int = None) -> object:
        """
        Get a list of apps based on their category. If no subcategory is specified,
        the method returns a list with all the possible subcategories.
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
                logging.error('Error when listing app by category: {0}'.format(response.commands.displayErrorMessage))
            except AttributeError:
                logging.error('There was an error when listing app by category.')
        else:
            list_response = response.payload.listResponse

        return list_response

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
                logging.error('Error for search "{0}": {1}'.format(query, response.commands.displayErrorMessage))
            except AttributeError:
                logging.error('There was an error when searching for "{0}".'.format(query))
        else:
            try:
                doc = response.payload.searchResponse.doc[0]
            except IndexError:
                pass
            # If the result of the query doesn't contain the desired information.
            if not doc:
                doc = None
                logging.warning('There were no results when searching for "{0}". Try using "{1}".'.format(
                    response.payload.searchResponse.originalQuery,
                    response.payload.searchResponse.suggestedQuery))

        return doc

    def app_details(self, package_name: str) -> object:
        """
        Get the details for a certain app (identified by the package name) in the Google Play Store.
        :param package_name: The package name of the app (e.g. "com.example.myapp").
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
                logging.error('Error for app "{0}": {1}'.format(package_name, response.commands.displayErrorMessage))
            except AttributeError:
                logging.error('There was an error when requesting details for app "{0}".'.format(package_name))
        else:
            details = response.payload.detailsResponse

        return details

    def download(self, package_name: str, file_name: str = None) -> bool:
        """
        Download a certain app (identified by the package name) from the Google Play Store.
        :param package_name: The package name of the app (e.g. "com.example.myapp").
        :param file_name: The location where to save the downloaded app (by default "package_name.apk").
        :return: True if the file was downloaded correctly, False otherwise.
        """

        # Set the default file name if none is provided.
        if not file_name:
            file_name = '{0}.apk'.format(package_name)

        # Get the app details before downloading it.
        details = self.app_details(package_name)

        if details is None:
            logging.error('Can\'t proceed with the download. There was an error when '
                          'requesting details for app "{0}".'.format(package_name))
            return False

        version_code = details.docV2.details.appDetails.versionCode
        offer_type = details.docV2.offer[0].offerType

        # Prepare the query.
        path = 'purchase'
        data = 'ot={0}&doc={1}&vc={2}'.format(offer_type, package_name, version_code)

        # Execute the first query to get the download link.
        response = self._execute_request(path, data)

        # If the query went completely wrong.
        if 'payload' not in self.protobuf_to_dict(response):
            try:
                logging.error('Error for app "{0}": {1}'.format(package_name, response.commands.displayErrorMessage))
            except AttributeError:
                logging.error('There was an error when requesting the download link '
                              'for app "{0}".'.format(package_name))
            return False
        else:
            # The url where to download the apk file.
            temp_url = response.payload.buyResponse.purchaseStatusResponse.appDeliveryData.downloadUrl

            # Additional files (.obb) to be downloaded with the apk.
            additional_files = [additional_file.downloadUrl for additional_file in
                                response.payload.buyResponse.purchaseStatusResponse.appDeliveryData.additionalFile]

        try:
            cookie = response.payload.buyResponse.purchaseStatusResponse.appDeliveryData.downloadAuthCookie[0]
        except IndexError:
            logging.error('DownloadAuthCookie was not received for "{0}".'.format(package_name))
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
        with open(file_name, 'wb') as f:
            for chunk in tqdm(response.iter_content(chunk_size=chunk_size), total=(apk_size // chunk_size),
                              dynamic_ncols=True, unit=' KB', desc=('Downloading {0}'.format(package_name)),
                              bar_format='{l_bar}{bar}|[{elapsed}<{remaining}, {rate_fmt}]'):
                if chunk:
                    f.write(chunk)
                    f.flush()

        # Check if the entire file was downloaded correctly.
        if apk_size != os.path.getsize(file_name):
            logging.error('Download not completed for "{0}". The file "{1}" is corrupted '
                          'and will be removed.'.format(package_name, file_name))
            try:
                os.remove(file_name)
            except OSError:
                logging.warning('The file "{0}" is corrupted and should be removed manually.'.format(file_name))

            return False

        # Save the additional files for the apk.
        for index, file_url in enumerate(additional_files):

            # Execute another query to get the actual file.
            response = requests.get(file_url, headers=headers, cookies=cookies, verify=True, stream=True)

            chunk_size = 1024
            file_size = int(response.headers['content-length'])

            additional_file_name = '{0}-additional-file-{1}.obb'.format(file_name, index + 1)

            # Download the apk file and save it, showing a progress bar.
            with open(additional_file_name, 'wb') as f:
                for chunk in tqdm(response.iter_content(chunk_size=chunk_size), total=(file_size // chunk_size),
                                  dynamic_ncols=True, unit=' KB',
                                  desc=('Downloading additional file {0}'.format(index + 1)),
                                  bar_format='{l_bar}{bar}|[{elapsed}<{remaining}, {rate_fmt}]'):
                    if chunk:
                        f.write(chunk)
                        f.flush()

            # Check if the entire additional file was downloaded correctly.
            if file_size != os.path.getsize(additional_file_name):
                logging.error('Download not completed for additional file {0} of "{1}". The file "{2}" is corrupted '
                              'and will be removed.'.format(index + 1, package_name, additional_file_name))
                try:
                    os.remove(additional_file_name)
                except OSError:
                    logging.warning('The file "{0}" is corrupted and should be removed manually.'
                                    .format(additional_file_name))

                return False

        return True
