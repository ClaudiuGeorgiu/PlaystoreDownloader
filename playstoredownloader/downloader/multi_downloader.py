import logging
from .downloader import DownloadError

logger = logging.getLogger(__name__)


class MultiDownloader:
    def __init__(self, package_list, downloader):
        self.package_list = package_list
        self.downloader = downloader

    def download(self):
        errors = False
        for package in self.package_list:
            result = self.downloader.download(package.strip(" '\""))
            if not result.success:
                logger.error(
                    "There was an error downloading package %s",
                    package,
                )
                errors = True
        if errors:
            raise DownloadError()
