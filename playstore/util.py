#!/usr/bin/env python
# coding: utf-8

import itertools
import logging
import time

from tqdm import tqdm

logger = logging.getLogger(__name__)


def retry(delays=(1, 2, 3, 5), exception=Exception):
    """
    Retry decorator.

    Retry the execution of the wrapped function/method in case of specific errors, for a specific number
    of times (specified by delays, in seconds).

    :param delays: The delays (in seconds) between consecutive executions of the wrapped function/method.
    :param exception: The exception to check (may be a tuple of exceptions to check). By default, all
                      the exceptions are checked.
    """

    def wrapper(function):
        def wrapped(*args, **kwargs):
            for delay in itertools.chain(delays, [None]):
                try:
                    return function(*args, **kwargs)
                except exception as e:
                    if delay is None:
                        logger.error("{0} (no more retries)".format(e))
                        raise
                    else:
                        logger.warning("{0} (retrying in {1}s)".format(e, delay))
                        time.sleep(delay)

        return wrapped

    return wrapper


# When iterating over list L, use "for element in show_list_progress(L, interactive=True)"
# to show a progress bar. When setting "interactive=False", no progress bar will be shown.
# While using this method, no other code should write to standard output.
def show_list_progress(
    the_list: list,
    interactive: bool = False,
    unit: str = "unit",
    total: int = None,
    description: str = None,
):
    if not interactive:
        return the_list
    else:
        if total:
            return tqdm(
                the_list,
                total=total,
                dynamic_ncols=True,
                unit=unit,
                desc=description,
                bar_format="{l_bar}{bar}|[{elapsed}<{remaining}, {rate_fmt}]",
            )
        else:
            return tqdm(
                the_list,
                dynamic_ncols=True,
                unit=unit,
                desc=description,
                bar_format="{l_bar}{bar}|[{elapsed}<{remaining}, {rate_fmt}]",
            )
