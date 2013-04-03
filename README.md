slithersentence
===============

Crawling and scraping to collect Chinese sentences. This is a preliminary prototype, directed at a single domain.

Version
-------

V. 0.2, 20130402.


To use
------

1. Initialize database

    sqlite3 crawl_worldjournal.db < create_table.sqlscript
2. Create directory for downloads

    mkdir CRAWLED_PAGES
2. Run `downloader.py` and `link_collector.py` alternately. 
 * `downloader.py`: downloads pages and stores them in `CRAWLED_PAGES/`, compressed and using the MD5 hash of the content as the core of the file name; the candidate URLs are taken from the database `crawl_worldjournal.db`
 * `link_collector.py`: collects URLs from downloaded pages and stores them in the database `crawl_worldjournal.db`.


New as of this version
----------------------
1. Download and link-collecting functionality is in separate programs.
2. Functions are now highly modularized and specialized.
3. Reduced number of state attributes.


To do next
----------
1. Second class, parallel to Downloader but always instantiated within it, for dealing with links and nothing else.
2. Begin working with `pytest`.
3. Get rid of `verbose` state and begin using `logging` module.
3. Use extra table for dealing with the start page of the site, so as to keep it separate from all the other pages.
2. Attempt to generalize crawler to more sites.
3. Crawler should eventually use threads or independent processes (from shell?) to conduct continuous crawling; manage this with a queue.

Previous versions
-----------------
0.1, 20130325.


[end]
