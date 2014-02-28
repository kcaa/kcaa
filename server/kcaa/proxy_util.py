#!/usr/bin/env python

import datetime
import logging
import time

import dateutil.parser
import dateutil.tz
import requests


# Use this for creating the minimum datetime.
# Never use datetime.datetime.min, as it's not aware of timezones.
DATETIME_MIN = datetime.datetime(
    datetime.MINYEAR, 1, 1, tzinfo=dateutil.tz.tzutc())


class HarManager(object):

    MAX_HAR_SIZE = 1024 * 1024  # 1 MiB

    def __init__(self, args, timeout):
        self._logger = logging.getLogger('kcaa.proxy_util')
        self.proxy_port = args.proxy.partition(':')[2]
        self.proxy_root = 'http://{}/proxy'.format(args.proxy_controller)
        self.proxy_port_root = '{}/{}'.format(self.proxy_root, self.proxy_port)
        self.proxy_har = '{}/har'.format(self.proxy_port_root)
        self.proxy_har_pageref = '{}/har/pageRef'.format(self.proxy_port_root)
        self.timeout = timeout
        self.reset_proxy()

    def reset_proxy(self):
        self.pageref = 1
        self.next_pageref = None
        self.old_pagerefs = set()
        self.last_page_size = 0
        self.last_accessed_time = DATETIME_MIN
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
        if r.status_code != requests.codes.NOT_FOUND:
            r.raise_for_status()
        r = requests.post(self.proxy_root, data={'port': self.proxy_port})
        r.raise_for_status()
        r = requests.put(self.proxy_har, data={'initialPageRef': self.pageref,
                                               'captureContent': 'true'})
        r.raise_for_status()

    def delete_old_pages(self):
        if not self.old_pagerefs:
            return
        old_pagerefs = ','.join(map(str, self.old_pagerefs))
        try:
            r = requests.delete('{}/{}'.format(self.proxy_har_pageref,
                                               old_pagerefs),
                                timeout=self.timeout)
            r.raise_for_status()
            self.old_pagerefs.clear()
        except:
            # We can safely ignore errors, because old pages don't affect the
            # behavior of get_current_page(). Just expect this will succeed
            # sometime in the future.
            self._logger.info('Failed to delete pages {}.'.format(
                old_pagerefs))

    def get_current_page(self):
        start = datetime.datetime.now()
        try:
            r = requests.get('{}?pageRef={}'.format(self.proxy_har,
                                                    self.pageref),
                             timeout=self.timeout)
            r.raise_for_status()
        except:
            self._logger.info('Failed to get page {}.'.format(self.pageref))
            return None, self.last_page_size
        fetch_span = datetime.datetime.now() - start

        # No Content-Length header?
        content_size = len(r.content)
        # HAR content should always be encoded in UTF-8, according to the spec.
        start = datetime.datetime.now()
        har = r.json(encoding='utf8')
        parse_span = datetime.datetime.now() - start

        if (content_size >= 2 * HarManager.MAX_HAR_SIZE or
                fetch_span.total_seconds() > 0.5 or
                parse_span.total_seconds() > 0.5):
            self._logger.debug('HAR page {} ({:.1f} KiB), fetched in {:.2f} '
                               'sec, parsed in {:.2f} sec.'.format(
                                   self.pageref,
                                   (1.0 / 1024) * content_size,
                                   fetch_span.total_seconds(),
                                   parse_span.total_seconds()))

        return har, content_size

    def get_current_page_and_create_next(self):
        # If there is no next page created yet, create it first.
        if self.next_pageref is None:
            next_pageref = self.pageref + 1
            try:
                r = requests.put(self.proxy_har_pageref,
                                 data={'pageRef': next_pageref},
                                 timeout=self.timeout)
                r.raise_for_status()
            except:
                self._logger.warn('Failed to create the next page {}.'.format(
                    next_pageref))
                return None, self.last_page_size
            # Set next_pageref to mark that the next page is created.
            self.next_pageref = next_pageref
        har, content_size = self.get_current_page()
        if not har:
            return None, self.last_page_size
        # If we get the whole content in the current page, we can move on to
        # the next page. The last page can be deleted.
        self.old_pagerefs.add(self.pageref)
        self.pageref = self.next_pageref
        self.next_pageref = None
        return har, 0

    def get_new_entries(self, har):
        entries = []
        last_accessed_time = DATETIME_MIN
        for entry in har['log']['entries']:
            started_datetime = dateutil.parser.parse(entry['startedDateTime'])
            if started_datetime <= self.last_accessed_time:
                continue
            if started_datetime > last_accessed_time:
                last_accessed_time = started_datetime
            entries.append(entry)
        if self.last_accessed_time < last_accessed_time:
            self.last_accessed_time = last_accessed_time
        return entries

    def get_updated_entries(self):
        self.delete_old_pages()
        if self.last_page_size >= HarManager.MAX_HAR_SIZE:
            har, self.last_page_size = self.get_current_page_and_create_next()
        else:
            har, self.last_page_size = self.get_current_page()
        return self.get_new_entries(har) if har else None
