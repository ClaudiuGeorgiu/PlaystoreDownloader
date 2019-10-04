#!/usr/bin/env python
# coding: utf-8

import itertools
import logging
import time

logger = logging.getLogger(__name__)


def retry(delays=(1, 2, 3, 5), exception=Exception):
    """
    Retry decorator.

    Retry the execution of the wrapped function/method in case of specific errors, for a specific number
    of times (specified by delays).

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
