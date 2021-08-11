#!/usr/bin/env python3

import logging

from playstoredownloader.playstore.playstore import Playstore
from playstoredownloader.playstore.meta import PackageMeta
from .out_dir import OutDir

logger = logging.getLogger(__name__)


class Downloader:

    def __init__(self, blobs, split_apks, credentials, out, tag):
        self.api = Playstore(credentials)
        self.blobs = blobs
        self.split_apks = split_apks
        self.out = out
        self.tag = tag

    def download(self, package_name):
        meta = PackageMeta(
            api=self.api,
            package_name=package_name.strip(" '\""),
        )
        out_dir = OutDir(self.out, tag=self.tag, meta=meta)
        return self.api.download(
            meta=meta,
            out_dir=out_dir,
            download_obb=self.blobs,
            download_split_apks=self.split_apks,
        )
