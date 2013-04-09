#!/usr/bin/env python3
# downloader.py
# 20130402, works
'''Prototype page-downloader for Chinese sites.

Prototype page-downloader for collecting webpages that are good candidates for
scraping Chinese sentences from.

'''

import os
import sys
import urllib.request
import bs4
import time
import datetime
import sqlite3
import hashlib
import bz2
import logging

import utils

url_core = 'worldjournal'

class Downloader(object):
    def __init__(self, logging_flag):
        app_name = __file__.split('.')[0]
        utils.set_up_logger(app_name, logging_flag)
        # Misc. class attributes
        self.soup = None
        self.hashed_soup = None
        self.compressed_soup = None
        self.cursor = None
        # Counters
        self.urlerrors = 0
        self.count_prospective_pages = 0
        self.count_saved = 0
        self.count_discarded_pages = 0
        # Timers
        self.start_time = time.time()
        self.request_time = 0
        self.disk_save_time = 0

    def summarize_run(self):
        '''Summarize the main events of this crawling run.'''
        elapsed = time.time() - self.start_time
        elapsed_str = str(datetime.timedelta(seconds=elapsed))
        indent = ' ' * 4
        print('\n\nTiming')
        print(indent + 'Time elapsed: {}.'.format(elapsed_str))
        print(indent + 'Time spent on HTTP requests: {0} or {1:.2f}%.'.
                format(str(datetime.timedelta(seconds=self.request_time)),
                       100 * self.request_time/elapsed))
        print(indent + 'Time spent saving to disk: {0} or {1:.2f}%.'.
                format(str(datetime.timedelta(seconds=self.disk_save_time)),
                       100 * self.disk_save_time/elapsed))
        print('Links and pages')
        print(indent + '{0}/{1} pages = ({2:d}%) stored to disk.'.
                format(self.count_saved, self.count_prospective_pages, 
                       utils.percentage(self.count_saved,
                                        self.count_prospective_pages)))
        print('Errors')
        print(indent + '{} pages discarded.'.format(self.count_discarded_pages))
        print(indent + '{} URLErrors.'.  format(self.urlerrors), end='')
        if self.urlerrors:
            print(indent + '''Consider running again until there are no '''
                    '''more URLErrors''')
        else:
            print('\n')
        with sqlite3.connect('crawl_' + url_core +
                '.db') as connection:
            cursor = connection.cursor()
            cursor = cursor.execute('''SELECT * FROM urls;''')
            print('{} unique records in database'.
                    format(len(cursor.fetchall())))
            cursor.close()

    def get_urls(self):
        '''Return a list of candidate URLs from the database.

        Assumes open SQLite3 connection.
        '''
        try:
            self.cursor = self.cursor.execute('''SELECT url FROM urls WHERE '''
                                              '''date_downloaded IS NULL;''')
        except Exception as e:
            logging.error(e)
        db_content = self.cursor.fetchall()
        return [i[0] for i in db_content]

    def request_page(self, url):
        '''Issue HTTP request for url argument'''
        request_time_start = time.time()
        try:
            retrieved_contents = (urllib.request.urlopen(url).  read().strip())
        except urllib.request.URLError as e:
            logging.error(str(e) + ' with URL = ' + url)
            self.urlerrors += 1
            print('|', end='')
            return ''
        self.request_time += time.time() - request_time_start
        return retrieved_contents

    def process_page(self, url, retrieved_contents):
        '''Decode page contents with Beautiful Soup,
        generating soup, its hash, and compressed form for saving to disk.

        In;  URL.

        Out: soup, hashed_soup, compressed_soup
        '''
        if retrieved_contents:
            self.soup = bs4.BeautifulSoup(retrieved_contents)
        else:
            logging.error('retrieved_contents is empty, with URL = ' + url)
        # Periodically soup.encode() raises recursion errors, hence the use of
        # try block.
        try:
            self.hashed_soup = hashlib.md5(self.soup.encode()).hexdigest()
            self.compressed_soup = bz2.compress(self.soup.encode())
        except Exception as e:
            self.hashed_soup = None
            self.compressed_soup = None
            logging.error(e)
            self.count_discarded_pages += 1
            print('|', end='')

    def store_page(self, url):
        '''Save webpage to disk and the name of file to database.

        In:  URL. Assumes open SQLite3 connection.

        Out: Page associated with URL is saved to disk under name derived from
             page's md5 hash.

             Hash itself is saved to database.

        '''
        if self.compressed_soup:
            start_time = time.time()
            # We save file first and update database afterwards in update_db(),
            #    to reduce chance of false positives in database.
            if url == 'http://' + url_core + '.com':
                filename = url_core + '_base_page_' + self.hashed_soup + '.bz2'
            else:
                filename = url_core + '_' + self.hashed_soup + '.bz2'
            with open(os.path.join('CRAWLED_PAGES', filename), 'wb') as f:
                try:
                    f.write(self.compressed_soup)
                    self.count_saved += 1
                    print('.', end='')
                except Exception as e:
                    logging.error(e)
                    self.count_discarded_pages += 1
                    print('|', end='')
                    return
                finally:
                    self.disk_save_time += time.time() - start_time
        else:
            logging.error('self.compressed_soup is empty, with URL = ' + url)
            return

    def update_db(self, url):
        '''Update the database record for a given URL with the hash of the
        content and the date/time of the download.

        Assumes open SQLite3 connection.
        '''
        now = datetime.datetime.strftime(datetime.datetime.now(),
                                         '%Y-%m-%d %H:%M:%S.%f')
        # Normally the start page of a site will not be crawled for content,
        # only for links. The variable want_content notes this state in the db.
        if url == 'http://' + url_core + '.com':
            # We will not store URL in database, allowing multiple entries. But
            # we will indicate that we will never ask for content from this
            # page; it is solely a source of URLs.
            want_content = 0
            try:
                self.cursor = self.cursor.execute('''
                        INSERT INTO urls (hash, date_url_added, 
                        date_downloaded, to_be_crawled_for_content)
                        VALUES (?, ?, ?, ?)''', 
                        (self.hashed_soup, now, now, want_content))
            except Exception as e:
                logging.error(str(e) + ' with URL = ' + url)
        else:
            want_content = 1
            try:
                self.cursor = self.cursor.execute('''
                        UPDATE urls
                        SET hash=?, date_downloaded=?,
                        to_be_crawled_for_content=?
                        WHERE url=?''',
                        (self.hashed_soup, now, want_content, url))
                self.count_prospective_pages += 1
                self.connection.commit()
            except Exception as e:
                logging.error(str(e) + ' with URL = ' + url)

    def cycle_through_fns(self, url):
        '''Calls the three main component methods in this procedure and then
        ensures the terminal output has been printed to the screen.
        '''
        retrieved_contents = self.request_page(url)
        self.process_page(url, retrieved_contents)
        self.store_page(url)
        self.update_db(url)
        sys.stdout.flush()

def main(logging_flag=''):
    downloader = Downloader(logging_flag)
    print('''\nWe print . for a page successfully saved and | for '''
            '''failure of any kind:''')
    # We use url_core in anticipation of generalizing this code for multiple
    # sites.
    with sqlite3.connect('crawl_' + url_core + '.db') \
            as downloader.connection:
        downloader.cursor = downloader.connection.cursor()
        # Deal with the top-level page, which always contains links but almost
        # never any unique textual content. This core page is always dealt with 
        # separately, since saving it is for the sake of culling links 
        # rather than culling content.
        print('\nFirst we handle the top-level page:')
        url = 'http://' + url_core + '.com'
        downloader.count_prospective_pages += 1
        downloader.cycle_through_fns(url)
        # Deal with candidate URLs from the database. These pages will
        # eventually be used for culling both content and links. We use a while
        # loop to try again on transient HTTP request failures.
        while True:
            downloader.urlerrors = 0
            candidate_url_list = downloader.get_urls()
            # Prepare to display real-time output
            if not candidate_url_list:
                print('\n\nThere are no prospective pages to download. '
                        'Exiting.')
                break
            print('\n\nProspective pages to download number {}:'. 
                    format(len(candidate_url_list)))
            for i in candidate_url_list:
                downloader.cycle_through_fns(i)
            if downloader.urlerrors:
                # Since we find that most URLErrors do not recur, we keep
                # trying until they succeed. In the future, we must find a way
                # to ensure that URLs that repeatedly fail are removed from
                # the cycle.
                print('\n\nNow retrying URLs that had URLErrors.', end='')
            else:
                break
    # Although "with" should make this unnecessary; we manually
    # close the cursor and the connection.
    downloader.cursor.close()
    downloader.connection.close()
    #
    # Report
    downloader.summarize_run()

if __name__ == '__main__':
    main(sys.argv[-1])
