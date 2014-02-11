#!/usr/bin/env python

import datetime
import json
import logging
import urllib2


class HarManager(object):

    def __init__(self, args):
        self._logger = logging.getLogger('kcaa.proxy_util')
        self.pageref = 1
        proxy_root = 'http://{}/proxy/{}'.format(args.proxy_controller,
                                                 args.proxy.partition(':')[2])
        self.har = '{}/har'.format(proxy_root)
        self.har_pageref = '{}/har/pageref'

    def _get(self, url):
        try:
            return urllib2.urlopen(url)
        except urllib2.URLError as e:
            self._logger.error('Proxy error: {}'.format(e))
            return None

    def get_next_page(self):
        # TODO: Create the next page
        start = datetime.datetime.now()
        # TODO: Retrieve only the current page
        data = self._get(self.har)
        # TODO: Delete the current page and move to the next one
        if not data:
            return None
        end = datetime.datetime.now()
        content = data.read()
        # No Content-Length header?
        content_size = len(content)
        self._logger.debug('Poke HAR ({:.1f} KiB) in {:.2f} seconds.'.format(
            (1.0 / 1024) * content_size, (end - start).total_seconds()))
        # HAR content should always be encoded in UTF-8, according to the spec.
        return json.loads(content, encoding='utf8')
