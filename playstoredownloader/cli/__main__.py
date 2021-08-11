from .argparser import get_cmd_args
from playstoredownloader.downloader.main import main

main(**vars(get_cmd_args()))
