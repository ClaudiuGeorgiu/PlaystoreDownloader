#!/usr/bin/env python
# coding: utf-8

import base64
import hashlib

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long


class EncryptedCredentials(object):

    # noinspection SpellCheckingInspection
    GOOGLE_PUB_KEY = b'AAAAgMom/1a/v0lblO2Ubrt60J2gcuXSljGFQXgcyZWveWLEwo6prwgi3iJIZdo' \
                     b'dyhKZQrNWp5nKJ3srRXcUW+F1BD3baEVGcmEgqaLZUNBjm057pKRI16kB0YppeG' \
                     b'x5qIQ5QjKzsR8ETQbKLNWgRY0QRNVz34kMJR3P/LgHax/6rmf5AAAAAwEAAQ=='

    def __init__(self, username: str, password: str):

        if not username or not password:
            raise ValueError('Username and/or password cannot be blank!')

        self.username = username
        self.password = password

    def get_encrypted_credentials(self):

        # Build the RSA key.

        binary_key = base64.b64decode(self.GOOGLE_PUB_KEY)

        i = bytes_to_long(binary_key[:4])
        mod = binary_key[4:4 + i]

        j = bytes_to_long(binary_key[i + 4:i + 4 + 4])
        exponent = binary_key[i + 8:i + 8 + j]

        rsa_key = RSA.construct((bytes_to_long(mod), bytes_to_long(exponent)))

        # Build the signature containing the encrypted credentials.

        cipher = PKCS1_OAEP.new(rsa_key)
        encrypted_credentials = cipher.encrypt((self.username + u'\x00' + self.password).encode('utf-8'))

        signature = bytearray(b'\x00')
        signature.extend(hashlib.sha1(binary_key).digest()[:4])
        signature.extend(encrypted_credentials)

        return base64.urlsafe_b64encode(signature)
