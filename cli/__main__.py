from .argparser import get_cmd_args
from downloader.main import main

main(**vars(get_cmd_args()))
