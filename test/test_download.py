#!/usr/bin/env python
# coding: utf-8

import os

import pytest

import download
from playstore.playstore import Playstore
# noinspection PyUnresolvedReferences
from test.test_playstore_api import playstore, VALID_PACKAGE_NAME, BAD_PACKAGE_NAME
# noinspection PyUnresolvedReferences
from test.test_session_fixtures import valid_credentials_path, download_folder_path


# noinspection PyShadowingNames
class TestDownload(object):

    def test_valid_download_specific_location(self, download_folder_path, valid_credentials_path, monkeypatch):

        downloaded_apk_path = '{0}.apk'.format(os.path.join(download_folder_path, VALID_PACKAGE_NAME))

        # Mock the command line parser.
        arguments = download.get_cmd_args(
            '"{0}" -c "{1}" -o "{2}"'.format(VALID_PACKAGE_NAME, valid_credentials_path, downloaded_apk_path).split())
        monkeypatch.setattr(download, 'get_cmd_args', lambda: arguments)

        download.main()

        assert os.path.isfile(downloaded_apk_path) is True

    def test_valid_download_default_location(self, valid_credentials_path, monkeypatch):
        # Mock the command line parser.
        arguments = download.get_cmd_args('"{0}" -c "{1}"'.format(VALID_PACKAGE_NAME, valid_credentials_path).split())
        monkeypatch.setattr(download, 'get_cmd_args', lambda: arguments)

        # If this runs without errors, the apk will be saved in the Downloads folder
        # (created in the same folder as download.py).
        download.main()

    def test_download_app_details_error(self, valid_credentials_path, monkeypatch):
        # Mock the command line parser.
        arguments = download.get_cmd_args('"{0}" -c "{1}"'.format(VALID_PACKAGE_NAME, valid_credentials_path).split())
        monkeypatch.setattr(download, 'get_cmd_args', lambda: arguments)

        # Mock the Playstore.
        monkeypatch.setattr(Playstore, 'app_details', lambda self, package: None)

        with pytest.raises(SystemExit) as err:
            download.main()
        assert err.value.code == 1

    def test_download_error(self, download_folder_path, valid_credentials_path, monkeypatch):
        downloaded_apk_path = '{0}.apk'.format(os.path.join(download_folder_path, 'error', VALID_PACKAGE_NAME))

        # Mock the command line parser.
        arguments = download.get_cmd_args(
            '"{0}" -c "{1}" -o "{2}"'.format(VALID_PACKAGE_NAME, valid_credentials_path, downloaded_apk_path).split())
        monkeypatch.setattr(download, 'get_cmd_args', lambda: arguments)

        # Mock the Playstore.
        monkeypatch.setattr(Playstore, 'download', lambda self, package, path: False)

        with pytest.raises(SystemExit) as err:
            download.main()
        assert err.value.code == 1
