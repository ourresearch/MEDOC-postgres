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
import argparse
import configparser
import pubmed
import doiboost
import sql_helper

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run stuff.")
    parser.add_argument('--pubmed', default=False, action='store_true', help="run the pubmed import")
    parser.add_argument('--doiboost', default=False, action='store_true', help="run the doiboost import")
    parser.add_argument('--skip-existing', default=False, action='store_true', help="skip existing pmids")
    parser.add_argument('--subset', nargs="?", type=str, help="subset of pubmed to pull in. valid responses: all, base, update")

    parsed_args = parser.parse_args()
    parsed_vars = vars(parsed_args)
    if parsed_vars["pubmed"]:
        lib_to_run = pubmed
        subset = parsed_vars.get("subset", "all")
    elif parsed_vars["doiboost"]:
        lib_to_run = doiboost

    # Create database if not exist
    lib_to_run.create_db_tables()

    # Get file list on NCBI
    gz_file_list = lib_to_run.get_file_list(subset)
    random.shuffle(gz_file_list)  # so it'll work better in parallel

    for file_to_download in gz_file_list:

        start_time = time.time()

        still_available = lib_to_run.mark_as_started(file_to_download)

        if still_available:
            # download file if not already
            file_downloaded = lib_to_run.download(file_name=file_to_download)

            # extract file
            file_content = lib_to_run.extract(file_name=file_to_download)

            # parse XML file to extract articles
            parsed_articles = lib_to_run.parse(file_content)

            # store the results in the DB
            lib_to_run.store_results(parsed_articles, file_to_download, file_downloaded, parsed_vars["skip-existing"])

            lib_to_run.mark_as_finished(file_to_download)
            if file_to_download:
                lib_to_run.remove_downloaded_file(file_name=file_to_download)

        print('Total time for file {}: {} min\n'.format(file_to_download, round((time.time() - start_time) / 60, 2)))


