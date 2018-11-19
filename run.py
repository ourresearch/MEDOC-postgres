#!/usr/bin/env python3
# coding: utf8

# ==============================================================================
# Title: medoc
# Description: medoc launch
# Author: Emeric Dynomant
# Contact: emeric.dynomant@omictools.com
# Date: 11/08/2017
# Language release: python 3.5.2
# ==============================================================================

import os
import re
import sys
import time
import random
import configparser
import pubmed
import sql_helper


if __name__ == '__main__':
    # Create database if not exist
    pubmed.create_db_tables()

    # Get file list on NCBI
    gz_file_list = pubmed.get_file_list()
    random.shuffle(gz_file_list)  # so it'll work better in parallel

    for file_to_download in gz_file_list:

        start_time = time.time()

        still_available = pubmed.mark_as_started(file_to_download)

        if still_available:
            # download file if not already
            file_downloaded = pubmed.download(file_name=file_to_download)

            # extract file
            file_content = pubmed.extract(file_name=file_to_download)

            # parse XML file to extract articles
            articles = pubmed.parse(data=file_content)

            # store the results in the DB
            pubmed.store_results(articles, file_to_download, file_downloaded)

            pubmed.mark_as_finished(file_to_download)
            if file_to_download:
                pubmed.remove_downloaded_file(file_name=file_to_download)

        print('Total time for file {}: {} min\n'.format(file_to_download, round((time.time() - start_time) / 60, 2)))

