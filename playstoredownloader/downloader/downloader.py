#!/usr/bin/env python3

import logging

from playstoredownloader.downloader.out_dir import OutDir
from playstoredownloader.playstore.meta import PackageMeta
from playstoredownloader.playstore.playstore import Playstore

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """An unspecified error when downloading a package."""


class DownloadResult:
    def __init__(self, success):
        self.success = success

    def raise_for_failures(self):
        if not self.success:
            raise DownloadError()


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
        result = self.api.download(
            meta=meta,
            out_dir=out_dir,
            download_obb=self.blobs,
            download_split_apks=self.split_apks,
        )
        return DownloadResult(result)
