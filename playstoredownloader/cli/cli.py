from .argparser import get_cmd_args
from playstoredownloader.downloader.main import main


def cli():
    main(**vars(get_cmd_args()))
