#!/usr/bin/env python3

import os

import pytest

import download
from playstore.playstore import Playstore

# noinspection PyUnresolvedReferences
from test.test_playstore_api import (
    playstore,
    VALID_PACKAGE_NAME,
    BAD_PACKAGE_NAME,
    APK_WITH_OBB,
    APK_WITH_SPLIT_APK,
)

# noinspection PyUnresolvedReferences
from test.test_session_fixtures import (
    valid_credentials_path,
    wrong_credentials_path,
    download_folder_path,
)


# noinspection PyShadowingNames
class TestDownload(object):
    def test_valid_download_specific_location(
        self, download_folder_path, valid_credentials_path, monkeypatch
    ):
        downloaded_apk_path = (
            f"{os.path.join(download_folder_path, VALID_PACKAGE_NAME)}.apk"
        )

        # Mock the command line parser.
        arguments = download.get_cmd_args(
            f'"{VALID_PACKAGE_NAME}" '
            f'-c "{valid_credentials_path}" '
            f'-o "{downloaded_apk_path}"'.split()
        )
        monkeypatch.setattr(download, "get_cmd_args", lambda: arguments)

        download.main()

        assert os.path.isfile(downloaded_apk_path) is True

    def test_valid_download_specific_location_with_tag(
        self, download_folder_path, valid_credentials_path, monkeypatch
    ):
        downloaded_apk_path = (
            f"{os.path.join(download_folder_path, VALID_PACKAGE_NAME)}.apk"
        )
        downloaded_apk_path_with_tag = (
            f"{os.path.join(download_folder_path, f'[TEST] {VALID_PACKAGE_NAME}')}.apk"
        )

        # Mock the command line parser.
        arguments = download.get_cmd_args(
            f'"{VALID_PACKAGE_NAME}" '
            f'-c "{valid_credentials_path}" '
            f'-o "{downloaded_apk_path}" -t "TEST"'.split()
        )
        monkeypatch.setattr(download, "get_cmd_args", lambda: arguments)

        download.main()

        assert os.path.isfile(downloaded_apk_path_with_tag) is True

    def test_valid_download_default_location(self, valid_credentials_path, monkeypatch):
        # Mock the command line parser.
        arguments = download.get_cmd_args(
            f'"{VALID_PACKAGE_NAME}" -c "{valid_credentials_path}"'.split()
        )
        monkeypatch.setattr(download, "get_cmd_args", lambda: arguments)

        # If this runs without errors, the apk will be saved in the Downloads folder
        # (created in the same folder as download.py).
        download.main()

    def test_valid_download_additional_files(self, valid_credentials_path, monkeypatch):
        # Mock the command line parser.
        arguments = download.get_cmd_args(
            f'"{APK_WITH_OBB}" -b -c "{valid_credentials_path}"'.split()
        )
        monkeypatch.setattr(download, "get_cmd_args", lambda: arguments)

        # If this runs without errors, the apk and the additional files will be saved
        # in the Downloads folder (created in the same folder as download.py).
        download.main()

    def test_valid_download_split_apk(self, valid_credentials_path, monkeypatch):
        # Mock the command line parser.
        arguments = download.get_cmd_args(
            f'"{APK_WITH_SPLIT_APK}" -s -c "{valid_credentials_path}"'.split()
        )
        monkeypatch.setattr(download, "get_cmd_args", lambda: arguments)

        # If this runs without errors, the apk and the split apk(s) will be saved in
        # the Downloads folder (created in the same folder as download.py).
        download.main()

    def test_download_app_details_error(self, valid_credentials_path, monkeypatch):
        # Mock the command line parser.
        arguments = download.get_cmd_args(
            f'"{VALID_PACKAGE_NAME}" -c "{valid_credentials_path}"'.split()
        )
        monkeypatch.setattr(download, "get_cmd_args", lambda: arguments)

        # Mock the Playstore.
        monkeypatch.setattr(Playstore, "app_details", lambda self, package: None)

        with pytest.raises(SystemExit) as err:
            download.main()
        assert err.value.code == 1

    def test_download_error(
        self, download_folder_path, valid_credentials_path, monkeypatch
    ):
        downloaded_apk_path = (
            f"{os.path.join(download_folder_path, 'error', VALID_PACKAGE_NAME)}.apk"
        )

        # Mock the command line parser.
        arguments = download.get_cmd_args(
            f'"{VALID_PACKAGE_NAME}" '
            f'-c "{valid_credentials_path}" '
            f'-o "{downloaded_apk_path}"'.split()
        )
        monkeypatch.setattr(download, "get_cmd_args", lambda: arguments)

        # Mock the Playstore.
        monkeypatch.setattr(
            Playstore,
            "download",
            lambda self, package, path, download_obb, download_split_apks: False,
        )

        with pytest.raises(SystemExit) as err:
            download.main()
        assert err.value.code == 1

    def test_download_wrong_credentials(self, wrong_credentials_path, monkeypatch):
        # Mock the command line parser.
        arguments = download.get_cmd_args(
            f'"{VALID_PACKAGE_NAME}" -c "{wrong_credentials_path}"'.split()
        )
        monkeypatch.setattr(download, "get_cmd_args", lambda: arguments)

        with pytest.raises(SystemExit) as err:
            download.main()
        assert err.value.code == 1
