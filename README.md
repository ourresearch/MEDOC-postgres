# medoc (MEdline DOwnloading Contrivance)

More information about medoc on OMICTools website or on medoc's publication on arXiv.org:

* https://arxiv.org/abs/1710.06590

* https://omictools.com/medline-downloading-contrivance-tool


## About medoc

### Development

Thanks to [rafspiny](https://github.com/rafspiny) for his multiple corrections and feedback !

### What is MEDLINE?

[MEDLINE](https://www.nlm.nih.gov/bsd/pmresources.html) is a database of scientitifc articles released by the NIH. [Pubmed](https://www.ncbi.nlm.nih.gov/pubmed/) is the most common way to query this database, used daily by many scientists around the world.

The NIH provides free APIs to build automatic queries, however a relational database could be more efficient.

The aim of this project is to download XML files provided by MEDLINE on a FTP and to build a relational database with their content.


## Launch

### Clone this repository

The first step is to clone this Github repository on your local machine.

Open a terminal:

	git clone "https://github.com/Impactstory/medoc-postgres"
	cd ./medoc-postgres

### Setup

Here prerequisites and installation procedures will be discussed.

#### Prerequisites 

XML parsing libraries may be needed. 

You can install them on any Debian-derived system with:

	sudo apt-get install libxml2-dev libxslt1-dev zlib1g-dev

You may also need `python-dev`. You can also install it with the same command:

	sudo apt-get install python-dev

#### Installation

Run the following command from the medoc folder.

    pip3 install pipenv
    pip3 install -r requirements.txt

(on osx if you get an error you may need to do `unset PYTHONPATH` first, as per [this tip](https://stackoverflow.com/a/44466013/596939) ).

NOTE: If python3 is your default, you do not need to specify `python3` or `pip3` but just use `python` and `pip`.

#### venv

Run the following command from the medoc folder.

    pipenv shell


#### Configuration

Before you can run the code, you should set environment variable DATABASE_URL to match your database connection string.

It'll look something like this, with your values for all the uppercase parts in the value:

    export DATABASE_URL=postgres://USERNAME:PASSWORD@HOST:PORT/YOURDATABASENAME

If your computer has 16Go or more of RAM, you can set '_insert_command_limit_' to '1000' of greater in 'configuration.cfg'


### Launch the programm

Simply execute :

	python3 run.py

	
### Output

First line should be about database creation and number of files to download.

Then, a regular output for a file loading should look like:

	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - DOWNLOADING FILE
	Downloading baseline/medline17n0216.xml.gz ..
	Elapsed time: 12.32 sec for module: download
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - FILE EXTRACTION
	Elapsed time: 0.42 sec for module: extract
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - XML FILE PARSING
	Elapsed time: 72.47 sec for module: parse
	- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - SQL INSERTION
	10000 articles inserted for file baseline/medline17n0216.xml.gz
	20000 articles inserted for file baseline/medline17n0216.xml.gz
	30000 articles inserted for file baseline/medline17n0216.xml.gz
	Total time for file medline17n0216.xml.gz: 5.29 min



## Issues

__Program stop running because of 'Segmentation fault (core dumped)'__

Indexing a file with 30K article take some time and RAM (if you know other parser than LXML, more RAM-frieldy, do a PR). Go to the line:

	soup = BeautifulSoup(file_content, 'lxml')

Change '_lxml_' to '_html-parser_' and re-launch SETUP.py.

Or simply try to lower the '_insert_command_limit_' parameter, to insert values more often in the database, thus saving RAM usage.


__SQL insertions are taking really a lot of time (more than 15min / file)'__

drop the tables

Then, comment every line about indexes (_CREATE INDEX_) or foreigns keys (_ALTER TABLE_) into the SQL creation file. Indexes are slowing up insertions.

When the database is full, launch the indexes and alter commands once at a time.

__Problem installing lxml__

Make sure you have all the right dependencies installed

On Debian based machines try running:

	sudo apt-get install python-dev libxml2-dev libxslt1-dev zlib1g-dev


## On Heroku

Needs to be run on a large dyno to have enough memory.  Performance-L works well, smaller dynos may too.


## Improvements over previous version

In addition to porting to Postgres, some improvements have been made:
- author order is preserved
- orcid is stored
- dois are stored more reliably
- apostrophes in titles and abstracts are preserved
- structured abstracts are supported
- save all affiliations not just the first one (new table: medline_affiliations)
- save raw xml (new table: medline_raw_xml)