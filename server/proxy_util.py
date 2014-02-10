#!/usr/bin/env python

import json
import urllib2


class HarManager(object):

    def __init__(self, args):
        self.pageref = 1
        proxy_root = 'http://{}/proxy/{}'.format(args.proxy_controller,
                                                 args.proxy.partition(':')[2])
        self.har = '{}/har'.format(proxy_root)
        self.har_pageref = '{}/har/pageref'

    def get_next_page(self):
        try:
            data = urllib2.urlopen(self.har)
        except urllib2.URLError:
            return None
        d = len(data.read())
        return d
        return json.loads(data)
