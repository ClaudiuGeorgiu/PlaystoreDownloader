#!/usr/bin/env python
# coding: utf-8

import os
from urllib.parse import urlparse, parse_qs

import pytest

from playstore import playstore_proto_pb2 as playstore_protobuf
from playstore.playstore import Playstore
# noinspection PyUnresolvedReferences
from test.test_session_fixtures import valid_credentials_path, download_folder_path


VALID_PACKAGE_NAME = 'com.spotify.music'
BAD_PACKAGE_NAME = '<-bad_package_name->'
APK_WITH_OBB = 'com.mapswithme.maps.pro'


# noinspection PyShadowingNames
@pytest.fixture(scope='session')
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
            playstore._execute_request('ignore')

    #########################
    # Play Store categories #
    #########################

    def test_get_base_categories(self, playstore):
        categories = playstore.protobuf_to_dict(playstore.get_store_categories())['category']
        category_names = list(map(lambda x: parse_qs(urlparse(x['dataUrl']).query)['cat'][0], categories))
        assert all(cat in category_names for cat in ['EDUCATION', 'GAME', 'PRODUCTIVITY', 'SOCIAL'])

    def test_get_game_subcategories(self, playstore):
        subcategories = playstore.protobuf_to_dict(playstore.get_store_categories('GAME'))['category']
        subcategory_names = list(map(lambda x: parse_qs(urlparse(x['dataUrl']).query)['cat'][0], subcategories))
        assert all(cat in subcategory_names for cat in ['GAME_ACTION', 'GAME_MUSIC', 'GAME_RACING', 'GAME_SPORTS'])

    def test_get_bad_subcategories(self, playstore):
        result = playstore.protobuf_to_dict(playstore.get_store_categories('INVALID_CATEGORY'))
        assert 'category' not in result

    def test_get_categories_response_error(self, playstore, monkeypatch):
        # Simulate a bad response from the server.
        monkeypatch.setattr(Playstore, '_execute_request', lambda self, path: playstore_protobuf.DocV2())
        categories = playstore.get_store_categories()
        assert categories is None

    def test_list_app_by_valid_category(self, playstore):
        subcategories = playstore.protobuf_to_dict(playstore.list_app_by_category('PRODUCTIVITY'))['doc']
        subcategory_names = list(map(lambda x: x['docid'], subcategories))
        assert 'apps_topselling_free' in subcategory_names

    def test_list_app_by_valid_category_and_subcategory(self, playstore):
        apps = playstore.protobuf_to_dict(
            playstore.list_app_by_category('PRODUCTIVITY', 'apps_topselling_free', 5))['doc'][0]['child']
        assert len(apps) <= 5
        assert all(app['docid'] for app in apps)
        assert all(app['title'] for app in apps)

    def test_list_app_by_category_response_error(self, playstore, monkeypatch):
        # Simulate a bad response from the server.
        monkeypatch.setattr(Playstore, '_execute_request', lambda self, path: playstore_protobuf.DocV2())
        subcategories = playstore.list_app_by_category('PRODUCTIVITY')
        assert subcategories is None

    def test_list_app_by_bad_category(self, playstore):
        result = playstore.protobuf_to_dict(playstore.list_app_by_category('INVALID_CATEGORY'))
        assert not result

    def test_list_app_by_category_missing_category(self, playstore):
        with pytest.raises(TypeError):
            playstore.list_app_by_category()

    #####################
    # Play Store search #
    #####################

    def test_valid_search(self, playstore):
        results = playstore.protobuf_to_dict(playstore.search('music', 5))['child']
        assert len(results) <= 5
        assert all(result['docid'] for result in results)
        assert all(result['title'] for result in results)

    def test_search_response_error(self, playstore, monkeypatch):
        # Simulate a bad response from the server.
        monkeypatch.setattr(Playstore, '_execute_request', lambda self, path: playstore_protobuf.DocV2())
        results = playstore.search('music')
        assert results is None

    def test_search_empty_string(self, playstore):
        with pytest.raises(TypeError):
            playstore.search()

    ##########################
    # Play Store app details #
    ##########################

    def test_valid_app_details(self, playstore):
        assert playstore.app_details(VALID_PACKAGE_NAME).docV2.docid == VALID_PACKAGE_NAME

    def test_bad_app_details(self, playstore):
        assert playstore.app_details(BAD_PACKAGE_NAME) is None

    def test_app_details_response_error(self, playstore, monkeypatch):
        # Simulate a bad response from the server.
        monkeypatch.setattr(Playstore, '_execute_request', lambda self, path: playstore_protobuf.DocV2())
        details = playstore.app_details(VALID_PACKAGE_NAME)
        assert details is None

    def test_missing_app_details(self, playstore):
        with pytest.raises(TypeError):
            playstore.app_details()

    ###########################
    # Play Store app download #
    ###########################

    def test_download_valid_package_name(self, playstore, download_folder_path):
        result = playstore.download(VALID_PACKAGE_NAME,
                                    os.path.join(download_folder_path, '{0}.apk'.format(VALID_PACKAGE_NAME)))
        assert result is True

    def test_download_corrupted_apk(self, playstore, download_folder_path, monkeypatch):
        # Mock the function that gets the size of the file so that the downloaded
        # apk will be treated as corrupted.
        monkeypatch.setattr(os.path, 'getsize', lambda x: 1)

        # Simulate an error with the file deletion.
        # noinspection PyUnusedLocal
        def raise_os_error(ignore):
            raise OSError
        monkeypatch.setattr(os, 'remove', raise_os_error)

        result = playstore.download(VALID_PACKAGE_NAME,
                                    os.path.join(download_folder_path, '{0}.apk'.format(VALID_PACKAGE_NAME)))
        assert result is False

    def test_download_response_error(self, playstore, monkeypatch):
        # Simulate a bad response from the server.
        app_details = playstore.app_details(VALID_PACKAGE_NAME)
        monkeypatch.setattr(Playstore, 'app_details', lambda self, package: app_details)
        monkeypatch.setattr(Playstore, '_execute_request', lambda self, path, data: playstore_protobuf.DocV2())
        result = playstore.download(VALID_PACKAGE_NAME)
        assert result is False

    def test_download_cookie_error(self, playstore, monkeypatch):
        # Simulate a bad response from the server.
        app_details = playstore.app_details(VALID_PACKAGE_NAME)
        monkeypatch.setattr(Playstore, 'app_details', lambda self, package: app_details)
        monkeypatch.setattr(Playstore, '_execute_request', lambda self, path, data: playstore_protobuf.ResponseWrapper())
        monkeypatch.setattr(Playstore, 'protobuf_to_dict', lambda self, proto_obj: {'payload': 'ignore'})
        result = playstore.download(VALID_PACKAGE_NAME)
        assert result is False

    def test_download_bad_package_name(self, playstore):
        result = playstore.download(BAD_PACKAGE_NAME)
        assert result is False

    def test_download_missing_package_name(self, playstore):
        with pytest.raises(TypeError):
            playstore.download()
