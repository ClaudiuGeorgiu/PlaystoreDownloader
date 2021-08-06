from pathlib import Path
from .downloader import Downloader
from .multi_downloader import MultiDownloader

def main(package, blobs, split_apks, credentials, out, tag):
    try:
        download_from_file(package, blobs, split_apks, credentials, out, tag)
    except (UnicodeDecodeError, FileNotFoundError):
        download_package(package, blobs, split_apks, credentials, out, tag)

def download_from_file(packages_file, blobs, split_apks, credentials, out, tag):
    with open(packages_file, 'rt') as fd:
        downloader = Downloader(blobs, split_apks, credentials, out, tag)
        MultiDownloader(fd.read().split("\n"), downloader).download()
    
def download_package(package, blobs, split_apks, credentials, out, tag):
    downloader = Downloader(blobs, split_apks, credentials, out, tag)
    downloader.download(package)
