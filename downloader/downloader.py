#!/usr/bin/env python3

import logging
import os
import re
import sys
from pathlib import Path

from cli.argparser import get_cmd_args
from playstore.playstore import Playstore

# Logging configuration.
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s> [%(levelname)s][%(name)s][%(funcName)s()] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    level=logging.INFO,
)


class Downloader:
    default_folder = Path.cwd()
    filename_pattern = re.compile(r"[^\w\-_.\s]")
    deafult_fname_template = "{title} by {creator} - {package_name}.apk"

    def __init__(self, blobs, split_apks, credentials, out, tag):
        self.api = Playstore(credentials.strip(" '\""))
        self.blobs = blobs
        self.split_apks = split_apks
        self.out = out
        self.tag = tag

    def add_tag(self, filename):
        return f"{self.tag} {filename}" if self.tag else filename

    def get_filepath(self, details):
        if self.out:
            return self.get_provided_filepath(details)
        return self.get_default_filepath(details)

    def get_provided_filepath(self, details):
        dirname, filename = os.path.split(self.out)
        filename = self.add_tag(filename) if filename else self.get_default_filename
        return Path.joinpath(dirname, filename)

    def get_default_filepath(self, details):
        return self.default_folder.joinpath(self.get_default_filename(details))

    def get_default_filename(self, details):
        return self.add_tag(
            self.filename_pattern.sub(
                "_",
                self.deafult_fname_template.format(
                    title=details.title,
                    creator=details.creator,
                    package_name=details.docid,
                ),
            )
        )

    def download(self, package_name):
        package_name = package_name.strip(" '\"")
        details = self.api.app_details(package_name).docV2
        destination = self.get_filepath(details)
        return self.api.download(
            details.docid,
            destination,
            download_obb=True if self.blobs else False,
            download_split_apks=True if self.split_apks else False,
        )
