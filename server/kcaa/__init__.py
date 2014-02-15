#!/usr/bin/env python

import logging
import sys

import browser
import controller
import flags
import kcsapi
import kcsapi_util
import proxy_util
import server


# Log to stdout.
logger = logging.getLogger('kcaa')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
