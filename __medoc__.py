#!/usr/bin/env python3
# coding: utf8

# ==============================================================================
# Title: MEDOC
# Description: MEDOC launch
# Author: Emeric Dynomant
# Contact: emeric.dynomant@omictools.com
# Date: 11/08/2017
# Language release: python 3.5.2
# ==============================================================================

import os
import re
import sys
import time
import configparser
sys.path.append('./lib')
import MEDOC
import getters

this_file_path = os.path.dirname(os.path.realpath(__file__))
top_level_path = os.path.join(this_file_path, ".")  # depends on where this file is in hierarchy

def store_results(MEDOC, articles, parameters, file_to_download, file_downloaded):
    print('- ' * 30 + 'SQL INSERTION')

    #  Timestamp
    start_time_sql = time.time()

    #  Lists to create
    table_fields_lookup = getters.get_fields()
    values = {}
    values_tot = {}
    for table_name in table_fields_lookup:
        values_tot[table_name] = []

    articles_count = 0
    insert_limit = int(parameters['database']['insert_command_limit'])

    # Delete existing
    getters.delete_existing(articles, parameters)

    # Create a dictionary with data to INSERT for every article
    for raw_article in articles:

        #  Loading
        articles_count += 1
        if articles_count % 10000 == 0:
            print('{} articles inserted for file {}'.format(articles_count, file_to_download))

        article_cleaned = re.sub("'", "''", str(raw_article))
        article_INSERT_list = MEDOC.get_command(article=article_cleaned, gz=file_downloaded)

        # For every table in articles, loop to create global insert
        for insert_table in article_INSERT_list:
            table_name = insert_table['name']

            for (table_name, fields) in table_fields_lookup.items():
                if insert_table['name'] == table_name:
                    values_this_item = getters.get_values(table_name, fields, insert_table)
                    values_tot[table_name].append(values_this_item)

                    if (len(values_tot[table_name]) == insert_limit) or (articles_count == len(articles)):
                        getters.insert(table_name, fields, values_tot[table_name], parameters)
                        values_tot[table_name] = []

    # Write the remaining entries
    for table_name in table_fields_lookup:
        if len(values_tot[table_name]) > 0:
            getters.insert(table_name, fields, values_tot[table_name], parameters)

    for table_name in table_fields_lookup:
        values_tot[table_name] = []

    # remove file and add file_name to a list to ignore this file next time
    print(
        'Elapsed time: {} sec for module: {}'.format(round(time.time() - start_time_sql, 2), 'insert'))
    if file_to_download:
        MEDOC.remove(file_name=file_to_download)

    #  Flush RAM
    del articles
    del values_tot



if __name__ == '__main__':
    MEDOC = MEDOC.MEDOC()
    parameters = configparser.ConfigParser()
    parameters.read('./configuration.cfg')

    # Step A : Create database if not exist
    MEDOC.create_pubmedDB()

    # Step B: get file list on NCBI
    gz_file_list = MEDOC.get_file_list()
    gz_file_list.reverse()  # reverse for fun, get to the more recent stuff early

    for file_to_download in gz_file_list:

        start_time = time.time()
        insert_log_path = os.path.join(top_level_path, parameters['paths']['already_downloaded_files'])

        if file_to_download not in open(insert_log_path).read().splitlines():
            # Step C: download file if not already
            file_downloaded = MEDOC.download(file_name=file_to_download)

            # Step D: extract file
            file_content = MEDOC.extract(file_name=file_downloaded)

            # Step E: Parse XML file to extract articles
            articles = MEDOC.parse(data=file_content)

            # Step F: Store the results in the DB
            store_results(MEDOC, articles, parameters, file_to_download, file_downloaded)

            print('Total time for file {}: {} min\n'.format(file_to_download, round((time.time() - start_time) / 60, 2)))

