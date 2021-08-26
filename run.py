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
import requests

def upload_to_s3(filename, local_file):
    import boto3
    from pubmed import download_folder

    print("getting ready to upload", filename_to_download)

    s3_client = boto3.client("s3")

    print("have s3 client")

    bucket_name = "openalex-sandbox"
    local_file_with_path = "{}{}".format(download_folder, local_file)
    print(local_file_with_path)
    s3_client.upload_file(local_file_with_path, bucket_name, filename)
    print("file now at", "s3://{}/{}".format(bucket_name, filename))


if __name__ == "__main__":

    # parse XML file to extract articles

    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=26403857&tool=my_tool&email=my_email@example.com&format=xml"
    r = requests.get(url)
    file_content = r.text

    # lib_to_run = pubmed
    # 
    # print(file_content)
    # parsed_articles = lib_to_run.parse(file_content)
    # print(parsed_articles)
    #
    
    # store the results in the DB
    # lib_to_run.store_results(parsed_articles, filename_to_download, file_downloaded, parsed_vars["skipexisting"])


    parser = argparse.ArgumentParser(description="Run stuff.")
    parser.add_argument('--pubmed', default=False, action='store_true', help="run the pubmed import")
    parser.add_argument('--doiboost', default=False, action='store_true', help="run the doiboost import")
    parser.add_argument('--skipexisting', default=False, action='store_true', help="skip existing pmids")
    parser.add_argument('--subset', nargs="?", type=str, help="subset of pubmed to pull in. valid responses: all, base, update")

    parsed_args = parser.parse_args()
    parsed_vars = vars(parsed_args)
    if parsed_vars["pubmed"]:
        lib_to_run = pubmed
        subset = parsed_vars.get("subset", "all")
    elif parsed_vars["doiboost"]:
        lib_to_run = doiboost

    # # Create database if not exist
    # lib_to_run.create_db_tables()
    #
    # Get file list on NCBI
    gz_file_list = lib_to_run.get_file_list(subset)
    random.shuffle(gz_file_list)  # so it'll work better in parallel

    files_uploaded = 0

    for filename_to_download in gz_file_list:
        print(filename_to_download)

        start_time = time.time()

        local_file = lib_to_run.download(file_name=filename_to_download)
        print(local_file)
        upload_to_s3(filename_to_download, local_file)
        files_uploaded +=1
        print("files uploaded: {}".format(files_uploaded))

        # still_available = lib_to_run.mark_as_started(filename_to_download)

        # if still_available:
            # download file if not already
            # file_downloaded = lib_to_run.download(file_name=filename_to_download)
            #
            #
            # # extract file
            # file_content = lib_to_run.extract(file_name=filename_to_download)
            # 
            # # parse XML file to extract articles
            # parsed_articles = lib_to_run.parse(file_content)
            # 
            # # store the results in the DB
            # lib_to_run.store_results(parsed_articles, filename_to_download, file_downloaded, parsed_vars["skipexisting"])

            # lib_to_run.mark_as_finished(filename_to_download)
            # if filename_to_download:
            #     lib_to_run.remove_downloaded_file(file_name=filename_to_download)

        print('Total time for file {}: {} min\n'.format(filename_to_download, round((time.time() - start_time) / 60, 2)))

# PATH=$(pyenv root)/shims:$PATH; unset PYTHONPATH
# echo 'PATH=$(pyenv root)/shims:$PATH' >> ~/.zshrc
# /Users/hpiwowar/.pyenv/versions/3.9.5/bin/python3  --version
# PYTHONPATH=/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages:
# python --version
