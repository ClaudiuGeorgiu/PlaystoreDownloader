from .argparser import get_cmd_args
from downloader.downloader import Downloader

Downloader(**vars(get_cmd_args()))
