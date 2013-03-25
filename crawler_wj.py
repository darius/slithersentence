#!/usr/bin/env python3
# crawler_wj.py
# 20130325
# Run with Python 3
'''Prototype crawler for Chinese sites.

Prototype crawler for collecting webpages that are good candidates for
scraping Chinese sentences from.

'''

import os
import sys
import re
import urllib.request
import urllib.error
import bs4
import time
import datetime
import sqlite3
import hashlib
import bz2


class Crawler():
    def __init__(self, url_core, verbose, dump):
        # start-up flags
        self.verbose = verbose
        self.dump = dump
        # Misc. class attributes
        self.found = []
        self.url_core = 'worldjournal'
        self.start_url = 'http://' + url_core + '.com'
        self.retrieved_contents = None
        self.soup = None
        self.now = None
        self.candidate_url_list = None
        self.chinese_marker_list = ['的', '个', '個', '了', '：', '。', '！',
                '？', '这', '這', '們', '们', '着', '呢', '，', '、', '；',
                '（', '）', '《', '》', '「', '」']
        self.chinese_markers = re.compile('|'.join(self.chinese_marker_list))
        # Counters
        self.non_unique = 0
        self.urlerrors = 0
        self.count_crawled = 0
        self.count_saved = 0
        self.count_discarded_pages = 0
        # Timers
        self.crawl_time = 0
        self.disk_save_time = 0

    def debug_print(self, *args, end='\n'):
        '''Print special debugging messages if -v flag is set at start-up.'''
        if self.verbose:
            print(*args, end='\n')

    def dump_urls(self, *args):
        '''Dump whole database if -v flag is set at start-up.'''
        if self.dump:
            with sqlite3.connect('crawl_' + self.url_core +
                    '.db') as connection:
                cursor = connection.cursor()
                cursor = cursor.execute('''SELECT * FROM urls;''')
                for i in cursor.fetchall():
                    print(i)

    def add_urls(self):
        '''Attempt to add each candidate URL to the database'''
        with sqlite3.connect('crawl_' + self.url_core +
                '.db') as connection:
            cursor = connection.cursor()
            if self.candidate_url_list:
                for url in self.candidate_url_list:
                    # flush output, since we have had a problem with this
                    sys.stdout.flush()
                    # strip irrelevant reference from URL end; always follows ?
                    url = url.split('?')[0]
                    # if relative URL, add prefix
                    if 'http' not in url:
                        whole_url = self.start_url + url
                    else:
                        whole_url = url
                    # insert (uniquely only) into db
                    try:
                        cursor = cursor.execute(
                                '''INSERT INTO urls (url, dateadded)
                                VALUES (?, ?)''',
                                (whole_url, self.now) )
                        print('.', end='')
                    except Exception as e:
                        self.debug_print('''{0}\n    {1}\n    continuing\n'''.
                                format(e, whole_url))
                        self.non_unique += 1
                        print('|', end='')
                        # flush output, since we have had a problem with this
                        sys.stdout.flush()
                        continue
                    self.found.append(whole_url)

    def get_url_from_tag(self, tag):
        '''From an <a ... href...> tag return the URL alone.'''
        try:
            link = tag.attrs['href']
            if 'http' not in link:
                return (self.start_url + link)
            else:
                return link
        except Exception as e:
            self.report_issue(e, tag, True)

    def follow_links(self):
        '''Generate a list of candidate URLs from the database.'''
        with sqlite3.connect('crawl_' + self.url_core + '.db') as connection:
            cursor = connection.cursor()
            try:
                cursor = cursor.execute('''SELECT url FROM urls WHERE
                        datecrawledforlinks IS NULL;''')
            except Exception as e:
                self.debug_print('''{0}'''.format(e))
                self.report_issue(e, 'follow_links()', True)
            db_content = cursor.fetchall()
            print('Prospective uncrawled URLs number', len(db_content))
            self.candidate_url_list = [i[0] for i in db_content]

    def report_issue(self, issue, item, continuing=False):
        '''Print an issue to STDOUT.

        Print to STDOUT an "issue" (typically an exception), an associated
        item, and (optionally) whether the process is supposed to continue.

        '''
        indent = ' ' * 4
        if continuing:
            last_word = indent + 'continuing'
        else:
            last_word = ''
        print('\n{0}\n{1}while dealing with: {1}\n{2}\n'.
                format(issue, indent, item, last_word))

    def store_me(self, url):
        '''Save webpage to disk and the name of file to database.


        In:  URL.

        Out: Page associated with URL is saved to disk under name derived from
             page's md5 hash.

             Hash itself is saved to database.

        '''
        self.now = datetime.datetime.strftime(datetime.datetime.now(),
                '%Y-%m-%d %H:%M:%S.%f')
        start_time = time.time()
        # Periodically soup.encode() raises recursion errors, hence the use of
        # try block.
        try:
            hashed_soup = hashlib.md5(self.soup.encode()).hexdigest()
            compressed_soup = bz2.compress(self.soup.encode())
        except Exception as e:
            self.report_issue(e, url, True)
            self.count_discarded_pages += 1
            return
        if not len(compressed_soup):
            print('compressed_soup is empty\n', url)
            return
        with open(os.path.join('CRAWLED_PAGES', self.url_core + '_' +
                hashed_soup + '.bz2'), 'wb') as f:
            try:
                f.write(compressed_soup)
                self.count_saved += 1
            except Exception as e:
                self.report_issue(e, url, True)
                self.count_discarded_pages += 1
                return
        self.disk_save_time += time.time() - start_time
        with sqlite3.connect('crawl_' + self.url_core + '.db') as connection:
            cursor = connection.cursor()
            try:
                cursor = cursor.execute('''
                        UPDATE urls
                        SET hash=?, datecrawledforlinks=?
                        WHERE url=?''',
                        (hashed_soup, self.now, url))
                self.count_crawled += 1
            except Exception as e:
                self.report_issue(e, url, True)

    def crawl_me(self, url):
        '''Generate a list of candidate URLs from the URL passed in.


        Also, update the database for the URL passed in, so that it
       is not crawled again.

        '''
        crawl_time_start = time.time()
        try:
            self.retrieved_contents = (urllib.request.urlopen(url).
                    read().strip())
        except urllib.request.URLError as e:
            self.report_issue(e, url, True)
            self.urlerrors += 1
        if not self.retrieved_contents:
            print('self.retrieved_contents is empty\n', url)
            return
        self.soup = bs4.BeautifulSoup(self.retrieved_contents)
        self.crawl_time += time.time() - crawl_time_start
        self.store_me(url)
        self.candidate_url_list = [self.get_url_from_tag(i)
                for i in self.soup.select('a[href^="/view"]')]

    def summarize_run(self):
        '''Summarize the main events of this crawling run.'''
        elapsed = time.time() - self.start_time
        elapsed_str = str(datetime.timedelta(seconds=elapsed))
        print('\n\nTiming')
        print('    Time elapsed: {}.'.format(elapsed_str))
        print('    Time spent on HTTP requests: {0} or {1:.2f}%.'.
                format(str(datetime.timedelta(seconds=self.crawl_time)),
                    100 * self.crawl_time/elapsed))
        print('    Time spent saving to disk: {0} or {1:.2f}%.'.
                format(str(datetime.timedelta(seconds=self.disk_save_time)),
                    100 * self.disk_save_time/elapsed))
        print('Links and pages')
        print('    {} links added this run.'.format(len(self.found)))
        print('    {} non-unique links ignored.'.format(self.non_unique))
        print('    {} pages scraped for links.'.format(self.count_crawled))
        print('    {} pages stored to disk.'.format(self.count_saved))
        print('Errors')
        print('    {} pages discarded.'.format(self.count_discarded_pages))
        print('    {0} URLErrors.'.  format(self.urlerrors))
        with sqlite3.connect('crawl_' + self.url_core +
                '.db') as connection:
            cursor = connection.cursor()
            cursor = cursor.execute('''SELECT * FROM urls;''')
            print('{} unique records in database'.
                    format(len(cursor.fetchall())))

def main(url_core='worldjournal', verbose=False, dump=False):
    crawler = Crawler(url_core, verbose, dump)
    crawler.start_time = time.time()
    #
    # Deal with the start URL
    crawler.crawl_me(crawler.start_url)
    print('''\nWe print . for a link added and | for a redundant link '''
            '''not added:\n''')
    crawler.add_urls()
    print('\n{0} unique links added on this run from the starting page.'.
            format(len(crawler.found)))
    print('{} non-unique links ignored.'.format(crawler.non_unique))
    #
    # Follow links from database and add more from each arrived-at page.
    print('\nNow beginning followed links.')
    crawler.follow_links()
    working_tag_list = crawler.candidate_url_list
    for i in working_tag_list:
        crawler.debug_print('attempting {}.'.format(i))
        crawler.crawl_me(i)
        crawler.add_urls()
    # Report
    crawler.summarize_run()

if __name__ == '__main__':
    main(verbose='-v' in sys.argv, dump='-d' in sys.argv)
