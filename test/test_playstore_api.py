#!/usr/bin/env python3

import os
from urllib.parse import urlparse, parse_qs

import pytest
from requests.exceptions import ChunkedEncodingError

from playstoredownloader.playstore import playstore_proto_pb2 as playstore_protobuf
from playstoredownloader.playstore.playstore import Playstore
from playstoredownloader.playstore.util import Util
from playstoredownloader.playstore.meta import PackageMeta
from playstoredownloader.downloader.out_dir import OutDir
# noinspection PyUnresolvedReferences
from test.test_session_fixtures import valid_credentials_path, download_folder_path

VALID_PACKAGE_NAME = "com.spotify.music"
BAD_PACKAGE_NAME = "<-bad_package_name->"
APK_WITH_OBB = "com.mapswithme.maps.pro"
APK_WITH_SPLIT_APK = "com.android.chrome"


@pytest.fixture(scope="function")
def playstore(valid_credentials_path):
    return Playstore(valid_credentials_path)


# noinspection PyShadowingNames
class TestApi(object):

    ####################
    # Play Store login #
    ####################

    def test_request_without_login(self, valid_credentials_path):
        # Simulate a request without the token generated during login.
        playstore = Playstore(valid_credentials_path)
        del playstore.auth_token
        with pytest.raises(RuntimeError):
            # noinspection PyProtectedMember
            playstore._execute_request("ignore")

    #########################
    # Play Store categories #
    #########################

    def test_get_base_categories(self, playstore):
        categories = playstore.protobuf_to_dict(playstore.get_store_categories())[
            "category"
        ]
        category_names = list(
            map(lambda x: parse_qs(urlparse(x["dataUrl"]).query)["cat"][0], categories)
        )
        assert all(
            cat in category_names
            for cat in ["EDUCATION", "GAME", "PRODUCTIVITY", "SOCIAL"]
        )

    def test_get_game_subcategories(self, playstore):
        subcategories = playstore.protobuf_to_dict(
            playstore.get_store_categories("GAME")
        )["category"]
        subcategory_names = list(
            map(
                lambda x: parse_qs(urlparse(x["dataUrl"]).query)["cat"][0],
                subcategories,
            )
        )
        assert all(
            cat in subcategory_names
            for cat in ["GAME_ACTION", "GAME_MUSIC", "GAME_RACING", "GAME_SPORTS"]
        )

    def test_get_bad_subcategories(self, playstore):
        result = playstore.protobuf_to_dict(
            playstore.get_store_categories("INVALID_CATEGORY")
        )
        assert "category" not in result

    def test_get_categories_response_error(self, playstore, monkeypatch):
        # Simulate a bad response from the server.
        monkeypatch.setattr(
            Playstore,
            "_execute_request",
            lambda self, path, query: playstore_protobuf.DocV2(),
        )
        categories = playstore.get_store_categories()
        assert categories is None

    def test_list_app_by_valid_category(self, playstore):
        subcategory_names = playstore.list_app_by_category("PRODUCTIVITY")
        assert "apps_topselling_free" in subcategory_names

    def test_list_app_by_valid_category_and_subcategory(self, playstore):
        doc = playstore.protobuf_to_dict(
            playstore.list_app_by_category("PRODUCTIVITY", "apps_topselling_free", 5)
        )["doc"][0]

        if "docid" in doc:
            # Old devices.
            apps = doc["child"]
        else:
            # New devices.
            apps = doc["child"][0]["child"]

        assert len(apps) > 1
        assert len(apps) <= 5
        assert all(app["docid"] for app in apps)
        assert all(app["title"] for app in apps)

    def test_list_app_by_category_response_error(self, playstore, monkeypatch):
        # Simulate a bad response from the server.
        monkeypatch.setattr(
            Playstore,
            "_execute_request",
            lambda self, path, query: playstore_protobuf.DocV2(),
        )
        subcategories = playstore.list_app_by_category("PRODUCTIVITY")
        assert subcategories is None

    def test_list_app_by_bad_category(self, playstore):
        result = playstore.list_app_by_category("INVALID_CATEGORY")
        assert not result

    def test_list_app_by_category_missing_category(self, playstore):
        with pytest.raises(TypeError):
            playstore.list_app_by_category()

    #####################
    # Play Store search #
    #####################

    def test_valid_search(self, playstore):
        results = playstore.protobuf_to_dict(playstore.search("music"))["child"]
        assert all(result["docid"] for result in results)
        assert all(result["title"] for result in results)

    def test_search_response_error(self, playstore, monkeypatch):
        # Simulate a bad response from the server.
        monkeypatch.setattr(
            Playstore,
            "_execute_request",
            lambda self, path, query: playstore_protobuf.DocV2(),
        )
        results = playstore.search("music")
        assert results is None

    def test_search_response_error_2(self, playstore, monkeypatch):
        # noinspection PyProtectedMember
        original = Playstore._execute_request

        def mock(*args, **kwargs):
            to_return = original(*args, **kwargs)
            del to_return.payload.searchResponse.doc[:]
            del to_return.preFetch[:]
            return to_return

        # Simulate a bad response from the server.
        monkeypatch.setattr(Playstore, "_execute_request", mock)
        results = playstore.search("music")
        assert results is None

    def test_search_empty_string(self, playstore):
        with pytest.raises(TypeError):
            playstore.search()

    def test_list_app_by_valid_developer(self, playstore):
        results = playstore.list_app_by_developer("Google LLC")
        assert len(results) >= 10

    ##########################
    # Play Store app details #
    ##########################

    def test_valid_app_details(self, playstore):
        api = Playstore()
        meta = PackageMeta(api, VALID_PACKAGE_NAME)
        assert (
            meta.app_details().docV2.docid == VALID_PACKAGE_NAME
        )

    def test_app_details_response_error(self, playstore, monkeypatch):
        # Simulate a bad response from the server.
        api = Playstore()
        meta = PackageMeta(api, VALID_PACKAGE_NAME)
        monkeypatch.setattr(
            Playstore,
            "_execute_request",
            lambda self, path, query: playstore_protobuf.DocV2(),
        )
        with pytest.raises(AttributeError):
            meta.app_details()

    def test_missing_app_details(self, playstore):
        api = Playstore()
        with pytest.raises(TypeError):
            PackageMeta(api, None)

    ###########################
    # Play Store app download #
    ###########################

    def test_download_valid_package_name(self, playstore, download_folder_path):
        api = Playstore()
        meta = PackageMeta(api, VALID_PACKAGE_NAME)
        result = playstore.download(
            meta,
            OutDir(download_folder_path, meta=meta),
            show_progress_bar=True,
        )
        assert result is True

    def test_download_corrupted_apk(self, playstore, download_folder_path, monkeypatch):
        # noinspection PyUnusedLocal
        api = Playstore()
        meta = PackageMeta(api, VALID_PACKAGE_NAME)
        
        def raise_exception(*args, **kwargs):
            raise ChunkedEncodingError()

        monkeypatch.setattr(Util, "show_list_progress", raise_exception)

        # Mock the function that gets the size of the file so that the downloaded
        # apk will be treated as corrupted.
        monkeypatch.setattr(os.path, "getsize", lambda x: 1)

        # Simulate an error with the file deletion.
        # noinspection PyUnusedLocal
        def raise_os_error(ignore):
            raise OSError

        monkeypatch.setattr(os, "remove", raise_os_error)

        result = playstore.download(
            VALID_PACKAGE_NAME,
            OutDir(download_folder_path, meta=meta),
        )
        assert result is False

    # TODO: split apk download seems not working anymore.

    # def test_download_corrupted_split_apk(
    #     self, playstore, download_folder_path, monkeypatch
    # ):
    #     original = Util.show_list_progress
    #
    #     def raise_exception(*args, **kwargs):
    #         if " split apk ".lower() not in kwargs["description"].lower():
    #             return original(*args, **kwargs)
    #         else:
    #             raise ChunkedEncodingError()
    #
    #     monkeypatch.setattr(Util, "show_list_progress", raise_exception)
    #
    #     result = playstore.download(
    #         APK_WITH_SPLIT_APK,
    #         os.path.join(download_folder_path, f"{APK_WITH_SPLIT_APK}.apk"),
    #         download_split_apks=True,
    #         show_progress_bar=False,
    #     )
    #     assert result is False

    def test_download_corrupted_obb(self, playstore, download_folder_path, monkeypatch):
        original = Util.show_list_progress
        api = Playstore()
        meta = PackageMeta(api, VALID_PACKAGE_NAME)

        def raise_exception(*args, **kwargs):
            if " .obb ".lower() not in kwargs["description"].lower():
                return original(*args, **kwargs)
            else:
                raise ChunkedEncodingError()

        monkeypatch.setattr(Util, "show_list_progress", raise_exception)

        result = playstore.download(
            APK_WITH_OBB,
            OutDir(download_folder_path, meta=meta),
            download_obb=True,
            show_progress_bar=False,
        )
        assert result is False

    def test_download_response_error(self, playstore, monkeypatch, download_folder_path):

        def mock(*args, **kwargs):
            return {}

        # Simulate a bad response from the server.
        monkeypatch.setattr(Playstore, "protobuf_to_dict", mock)
        api = Playstore()
        meta = PackageMeta(api, VALID_PACKAGE_NAME)
        result = playstore.download(
            meta,
            OutDir(download_folder_path, meta=meta),
        )
        assert result is False

    def test_download_response_error_2(self, playstore, monkeypatch, download_folder_path):
        # noinspection PyProtectedMember
        original = Playstore._execute_request

        def mock(*args, **kwargs):
            if mock.counter < 1:
                mock.counter += 1
                return original(*args, **kwargs)
            else:
                return playstore_protobuf.DocV2()

        mock.counter = 0

        # Simulate a bad response from the server.
        monkeypatch.setattr(Playstore, "_execute_request", mock)
        api = Playstore()
        meta = PackageMeta(api, VALID_PACKAGE_NAME)
        result = playstore.download(
            meta,
            OutDir(download_folder_path, meta=meta),
        )
        assert result is False

    def test_download_cookie_error(self, playstore, monkeypatch, download_folder_path):
        # noinspection PyProtectedMember
        original = Playstore._execute_request

        def mock(*args, **kwargs):
            to_return = original(*args, **kwargs)
            del to_return.payload.deliveryResponse.appDeliveryData.downloadAuthCookie[:]
            del to_return.payload.buyResponse.purchaseStatusResponse.appDeliveryData.downloadAuthCookie[
                :
            ]
            return to_return

        # Simulate a bad response from the server.
        monkeypatch.setattr(Playstore, "_execute_request", mock)
        api = Playstore()
        meta = PackageMeta(api, VALID_PACKAGE_NAME)
        result = playstore.download(
            meta,
            OutDir(download_folder_path, meta=meta),
        )
        assert result is False

    def test_download_bad_package_name(self, playstore, download_folder_path):
        api = Playstore()
        meta = PackageMeta(api, BAD_PACKAGE_NAME)
        result = playstore.download(
            meta,
            OutDir(download_folder_path, meta=meta),
        )
        assert result is False

    def test_download_missing_package_name(self, playstore):
        with pytest.raises(TypeError):
            playstore.download()
