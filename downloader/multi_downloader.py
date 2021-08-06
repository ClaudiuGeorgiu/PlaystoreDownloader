from .downloader import Downloader

class MultiDownloader:
    def __init__(self, package_list, downloader):
        self.package_list = package_list
        self.downloader = downloader

    def download(self):
        for package in self.package_list:
            self.downloader.download(package.strip(" '\""))
