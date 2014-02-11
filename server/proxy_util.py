#!/usr/bin/env python

import datetime
import logging

import requests


class HarManager(object):

    def __init__(self, args):
        self._logger = logging.getLogger('kcaa.proxy_util')
        self.pageref = 1
        proxy_root = 'http://{}/proxy/{}'.format(args.proxy_controller,
                                                 args.proxy.partition(':')[2])
        self._proxy_har = '{}/har'.format(proxy_root)
        self._proxy_har_pageref = '{}/har/pageRef'.format(proxy_root)

    def get_next_page(self):
        start = datetime.datetime.now()
        next_pageref = self.pageref + 1
        rp = requests.put(self._proxy_har_pageref,
                          data={'pageRef': next_pageref})
        rp.raise_for_status()
        rg = requests.get('{}?pageRef={}'.format(self._proxy_har,
                                                 self.pageref))
        rg.raise_for_status()
        rd = requests.delete('{}/{}'.format(self._proxy_har_pageref,
                                            self.pageref))
        rd.raise_for_status()
        self.pageref = next_pageref
        end = datetime.datetime.now()

        # No Content-Length header?
        content_size = len(rg.text)
        self._logger.debug('Poke HAR ({:.1f} KiB) in {:.2f} seconds.'.format(
            (1.0 / 1024) * content_size, (end - start).total_seconds()))
        # HAR content should always be encoded in UTF-8, according to the spec.
        return rg.json(encoding='utf8')
