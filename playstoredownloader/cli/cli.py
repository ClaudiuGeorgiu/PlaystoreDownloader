#!/usr/bin/env python3

from playstoredownloader.downloader.main import main
from playstoredownloader.cli.argparser import get_cmd_args


def cli():
    main(**vars(get_cmd_args()))
