#!/usr/bin/env python

import datetime
import logging
import time

import requests


class HarManager(object):

    def __init__(self, args):
        self._logger = logging.getLogger('kcaa.proxy_util')
        self.proxy_port = args.proxy.partition(':')[2]
        self.proxy_root = 'http://{}/proxy'.format(args.proxy_controller)
        self.proxy_port_root = '{}/{}'.format(self.proxy_root, self.proxy_port)
        self.proxy_har = '{}/har'.format(self.proxy_port_root)
        self.proxy_har_pageref = '{}/har/pageRef'.format(self.proxy_port_root)
        self.reset_proxy()

    def reset_proxy(self):
        self.pageref = 1
        # At the initial trial, the proxy controller may not be ready.
        last_error = None
        for _ in xrange(10):
            try:
                r = requests.delete(self.proxy_port_root)
                break
            except requests.ConnectionError as e:
                self._logger.info('Proxy contoller looks not ready. Retrying.')
                last_error = e
                time.sleep(1.0)
        else:
            raise last_error
        if r.status_code != requests.codes.not_found:
            r.raise_for_status()
        r = requests.post(self.proxy_root, data={'port': self.proxy_port})
        r.raise_for_status()
        r = requests.put(self.proxy_har, data={'initialPageRef': self.pageref,
                                               'captureContent': 'true'})
        r.raise_for_status()

    def get_next_page(self):
        start = datetime.datetime.now()
        next_pageref = self.pageref + 1
        rp = requests.put(self.proxy_har_pageref,
                          data={'pageRef': next_pageref})
        rp.raise_for_status()
        rg = requests.get('{}?pageRef={}'.format(self.proxy_har,
                                                 self.pageref))
        rg.raise_for_status()
        rd = requests.delete('{}/{}'.format(self.proxy_har_pageref,
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
