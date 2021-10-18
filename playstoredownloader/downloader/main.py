#!/usr/bin/env python3

from pathlib import Path

from playstoredownloader.downloader.downloader import Downloader
from playstoredownloader.downloader.multi_downloader import MultiDownloader


def get_default_credentials():
    credentials_path = Path("./private_credentials.json")
    if credentials_path.is_file():
        return credentials_path
    return Path("./credentials.json")


def main(
    package,
    blobs=False,
    split_apks=False,
    credentials=None,
    out_dir=Path.cwd() / "Downloads",
    tag=None,
):
    credentials = credentials or get_default_credentials()
    return download_packages(package, blobs, split_apks, credentials, out_dir, tag)


def download_packages(packages, blobs, split_apks, credentials, out, tag):
    downloader = Downloader(blobs, split_apks, credentials, out, tag)
    return MultiDownloader(packages, downloader).download()
