from pathlib import Path
from .downloader import Downloader
from .multi_downloader import MultiDownloader


def main(
    packages,
    blobs=False,
    split_apks=False,
    credentials=Path("./credentials.json"),
    dir=Path.cwd() / "Downloads",
    tag=None,
):
    return download_packages(packages, blobs, split_apks, credentials, dir, tag)


def download_packages(packages, blobs, split_apks, credentials, out, tag):
    downloader = Downloader(blobs, split_apks, credentials, out, tag)
    return MultiDownloader(packages, downloader).download()


def download_package(package, blobs, split_apks, credentials, out, tag):
    downloader = Downloader(blobs, split_apks, credentials, out, tag)
    downloader.download(package)
