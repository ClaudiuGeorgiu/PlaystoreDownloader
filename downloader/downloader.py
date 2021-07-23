#!/usr/bin/env python3

import logging
import os
import re
import sys

from playstore.playstore import Playstore
from cli.argparser import get_cmd_args

# Logging configuration.
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s> [%(levelname)s][%(name)s][%(funcName)s()] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    level=logging.INFO,
)
from pathlib import Path


class Downloader:
    downloaded_apk_default_location = Path.cwd()

    def __init__(self, blobs, split_apks, credentials, out, tag):
        self.api = Playstore(credentials.strip(" '\""))
        self.blobs = blobs
        self.split_apks = split_apks
        self.out = out
        self.tag = tag.strip(" '\"")

    def get_default_filepath(self, details):
        filename = re.sub(
            r"[^\w\-_.\s]",
            "_",
            f"{details['title']} by {details['creator']} - "
            f"{details['package_name']}.apk",
        )
        if self.tag:
            filename = f"{self.tag} {filename}"
        
        return self.downloaded_apk_default_location.joinpath(filename)

    def download(self, package_name):
        stripped_package_name = package_name.strip(" '\"")
        app = self.api.app_details(stripped_package_name).docV2
        details = {
            "package_name": app.docid,
            "title": app.title,
            "creator": app.creator,
        }
        destination = self.out or self.get_default_filepath(details)
        return self.api.download(
            details["package_name"],
            destination,
            download_obb=True if self.blobs else False,
            download_split_apks=True if self.split_apks else False,
        )
