#!/usr/bin/env python
# coding: utf-8

from playstore.credentials import EncryptedCredentials


def test_credentials():
    credentials_test = EncryptedCredentials('username', 'password')
    assert credentials_test.get_encrypted_credentials() is not None
