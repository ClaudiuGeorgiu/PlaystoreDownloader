#!/usr/bin/env python3

import argparse
import os

import pytest

import playstoredownloader.cli.cli as psdcli
from playstoredownloader.downloader.downloader import DownloadError
from playstoredownloader.playstore.meta import PackageMeta
from playstoredownloader.playstore.playstore import Playstore

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
class TestMain(object):
    def test_valid_download_specific_location(
        self, download_folder_path, valid_credentials_path, monkeypatch
    ):
        downloaded_apk_path = (
            f"{os.path.join(download_folder_path, VALID_PACKAGE_NAME)}.apk"
        )

        arguments = argparse.Namespace(
            package=[VALID_PACKAGE_NAME],
            credentials=valid_credentials_path,
            out_dir=download_folder_path,
        )
        monkeypatch.setattr(psdcli, "get_cmd_args", lambda: arguments)
        psdcli.cli()

        assert os.path.isfile(downloaded_apk_path) is True

    def test_valid_download_specific_location_with_tag(
        self, download_folder_path, valid_credentials_path, monkeypatch
    ):
        downloaded_apk_path_with_tag = (
            f"{os.path.join(download_folder_path, f'[TEST] {VALID_PACKAGE_NAME}')}.apk"
        )

        # Mock the command line parser.
        arguments = argparse.Namespace(
            package=[VALID_PACKAGE_NAME],
            credentials=valid_credentials_path,
            out_dir=download_folder_path,
            tag="TEST",
        )
        monkeypatch.setattr(psdcli, "get_cmd_args", lambda: arguments)
        psdcli.cli()

        assert os.path.isfile(downloaded_apk_path_with_tag) is True

    def test_valid_download_default_location(self, valid_credentials_path, monkeypatch):
        # Mock the command line parser.
        arguments = argparse.Namespace(
            package=[VALID_PACKAGE_NAME],
            credentials=valid_credentials_path,
        )
        monkeypatch.setattr(psdcli, "get_cmd_args", lambda: arguments)

        # If this runs without errors, the apk will be saved in the Downloads folder
        # (created in the same folder where this code is run).
        psdcli.cli()

    def test_valid_download_additional_files(self, valid_credentials_path, monkeypatch):
        # Mock the command line parser.
        arguments = argparse.Namespace(
            package=[APK_WITH_OBB],
            credentials=valid_credentials_path,
        )
        monkeypatch.setattr(psdcli, "get_cmd_args", lambda: arguments)

        # If this runs without errors, the apk and the additional files will be saved
        # in the Downloads folder (created in the same folder where this code is run).
        psdcli.cli()

    def test_valid_download_split_apk(self, valid_credentials_path, monkeypatch):
        # Mock the command line parser.
        arguments = argparse.Namespace(
            package=[APK_WITH_SPLIT_APK],
            credentials=valid_credentials_path,
        )
        monkeypatch.setattr(psdcli, "get_cmd_args", lambda: arguments)

        # If this runs without errors, the apk and the split apk(s) will be saved in
        # the Downloads folder (created in the same folder where this code is run).
        psdcli.cli()

    def test_download_app_details_error(self, valid_credentials_path, monkeypatch):
        # Mock the command line parser.
        arguments = argparse.Namespace(
            package=[VALID_PACKAGE_NAME],
            credentials=valid_credentials_path,
        )
        monkeypatch.setattr(psdcli, "get_cmd_args", lambda: arguments)

        # Mock the Playstore.
        monkeypatch.setattr(PackageMeta, "app_details", lambda self: None)

        with pytest.raises(RuntimeError):
            psdcli.cli()

    def test_download_error(
        self, download_folder_path, valid_credentials_path, monkeypatch
    ):

        # Mock the command line parser.
        arguments = argparse.Namespace(
            package=[VALID_PACKAGE_NAME],
            credentials=valid_credentials_path,
            out_dir=download_folder_path,
            tag="[TEST]",
        )
        monkeypatch.setattr(psdcli, "get_cmd_args", lambda: arguments)

        # Mock the Playstore.
        monkeypatch.setattr(
            Playstore,
            "download",
            lambda self, meta, out_dir, download_obb, download_split_apks: False,
        )

        with pytest.raises(DownloadError):
            psdcli.cli()

    def test_download_wrong_credentials(self, wrong_credentials_path, monkeypatch):
        # Mock the command line parser.
        arguments = argparse.Namespace(
            package=[VALID_PACKAGE_NAME],
            credentials=wrong_credentials_path,
        )
        monkeypatch.setattr(psdcli, "get_cmd_args", lambda: arguments)

        with pytest.raises(RuntimeError):
            psdcli.cli()
