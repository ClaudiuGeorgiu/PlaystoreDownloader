#!/usr/bin/env python
# coding: utf-8

import base64
import os

import pytest


@pytest.fixture(scope='session')
def credentials_path(tmpdir_factory):

    if 'TRAVIS' in os.environ and 'CI' in os.environ:
        # Travis CI testing.
        test_credentials = base64.b64decode(os.environ['CREDENTIALS']).decode('ascii')
    else:
        # Local testing. Make sure to use a valid json file with the credentials.
        with open('private_credentials.json', 'r') as file:
            test_credentials = file.read()

    tmp_credentials_file = tmpdir_factory.mktemp('credentials').join('credentials.json')

    with open(str(tmp_credentials_file), 'w') as file:
        file.write(test_credentials)

    return str(tmp_credentials_file)
