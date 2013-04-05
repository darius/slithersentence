slithersentence
===============

Crawling and scraping to collect Chinese sentences. This is a preliminary prototype, directed at a single domain.

Version
-------
 
V. 0.3, 20130405.
 
 
To use
------
 
1. Initialize database
```
    sqlite3 crawl_worldjournal.db < create_table.sqlscript
```

2. Create directory for downloads
```
    mkdir CRAWLED_PAGES
```
2. Run `downloader.py` and `link_collector.py` alternately.
 * `downloader.py`: downloads pages and stores them in `CRAWLED_PAGES/`, compressed and using the MD5 hash of the content as the core of the file name; the candidate URLs are taken from the database `crawl_worldjournal.db`
 * `link_collector.py`: collects URLs from downloaded pages and stores them in the database `crawl_worldjournal.db`.
3. These two programs can usefully be run in alternation until `link_collector.py` returns no links successfully added (the output is a string of all `|` and no `.`. Note that `downloader.py` will always return at least one successful download — the top-level page of the site.
 


New as of this version
----------------------
2. Functions are now highly modularized and specialized.
3. Reduced number of state attributes.
4. Eliminated the old `verbose` output flag and implemented `logging`.


To do next
----------
1. Second class, parallel to Downloader but always instantiated within it, for dealing with links and nothing else.
2. Begin working with `pytest`.
2. Third and fourth phase of this project: to collect the Chinese content and store it to database; and to extract distinct sentences from the content and store them to a separate database, which will be the foundation of linguistic study.
3. Use extra table for dealing with the start page of the site, so as to keep it separate from all the other pages. But perhaps this is not a good idea because we would like to be able to look up the URL and other data for each hash in a single table. Adding a second table would complicate that look-up — perhaps a third table, indexing all hashes against the other tables — would become necessary.
2. Attempt to generalize crawler to more sites.
3. Crawler should eventually use threads or independent processes (from shell?) to conduct continuous crawling; manage this with a queue.

Previous versions
-----------------
0.2, 20130402.

0.1, 20130325.


[end]
