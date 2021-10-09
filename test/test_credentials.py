#!/usr/bin/env python3

import pytest

from playstoredownloader.playstore.credentials import EncryptedCredentials


class TestCredentials(object):
    def test_valid_credentials(self):
        credentials_test = EncryptedCredentials("username", "password")
        assert credentials_test.get_encrypted_credentials() is not None

    def test_bad_credentials(self):
        with pytest.raises(ValueError):
            EncryptedCredentials("", "")
