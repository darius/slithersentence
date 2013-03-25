slithersentence
===============

Crawling and scraping to collect Chinese sentences. This is a preliminary prototype, directed at a single domain.

Version
-------

V. 0.1, 20130325.


To use
------

1. Initialize database
  sqlite3 crawl_worldjournal.db < create_table.sqlscript
2. Run `crawler_wj.py`. 

Results
-------

Program will begin crawling from www.worldjournal.com; it will collect links and then attempt to download each linked-to page into a directory `CRAWLED_PAGES`. 

Crawled pages are stored with `bz2` compression and using a hash as the body of the file name, to minimize the chance of overwriting. The hash has `worldjournal` prepended to identify the source of the content.

New as of this version
----------------------
1. This is the preliminary prototype.


To do next
----------
1. Separate scraper for the files downloaded for this domain.
2. Attempt to generalize crawler to more sites.
3. Crawler should eventually use threads or independent processes (from shell?) to conduct continuous crawling; manage this with a queue.

[end]
