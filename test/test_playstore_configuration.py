#!/usr/bin/env python
# coding: utf-8

import pytest

from playstore.playstore import Playstore
# noinspection PyUnresolvedReferences
from test.test_session_fixtures import \
    wrong_credentials_path, incomplete_configuration_path, corrupted_configuration_path


MISSING_CONFIGURATION_FILE = 'missing_configuration_path.json'


# noinspection PyShadowingNames
class TestConfiguration(object):

    def test_missing_configuration(self):
        with pytest.raises(SystemExit) as err:
            Playstore(MISSING_CONFIGURATION_FILE, debug=True)
        assert err.value.code == 1

    def test_bad_credentials(self, wrong_credentials_path):
        with pytest.raises(SystemExit) as err:
            Playstore(wrong_credentials_path)
        assert err.value.code == 1

    def test_incomplete_configuration(self, incomplete_configuration_path):
        with pytest.raises(SystemExit) as err:
            Playstore(incomplete_configuration_path)
        assert err.value.code == 1

    def test_corrupted_configuration(self, corrupted_configuration_path):
        with pytest.raises(SystemExit) as err:
            Playstore(corrupted_configuration_path)
        assert err.value.code == 1
