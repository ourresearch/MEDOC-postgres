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
import time
import gzip
import configparser
import requests
import datetime
from bs4 import BeautifulSoup
import urllib.parse
import psycopg2
from sql_helper import Query_Executor
from utils import clean_doi






this_file_path = os.path.dirname(os.path.realpath(__file__))
top_level_path = this_file_path  # depends on where this file is in hierarchy

insert_log_path = os.path.join(top_level_path, "log/inserted.log")
download_folder = os.path.join(top_level_path, "download_cache/")


def get_fields():
    fields = {}
    # pmid always first
    fields["doiboost_abstract"] = ['doi', 'abstract', 'provenance']
    fields["doiboost_author"] = ['doi', 'author_order', 'given', 'family', 'fullname', 'orcid', 'mag_id']
    fields["doiboost_affiliation"] = ['doi', 'author_order', 'affiliation_order', 'value', 'official_page', 'grid_id', 'microsoft_id', 'wikipedia_id']
    return fields


def get_values(table_name, fields, insert_table):
    values = []
    # For every fields
    for field in fields:
        for key, value in insert_table['value'].items():
            # If parsed value field == actual field
            if field == key:
                if value or str(value)=="0":
                    if isinstance(value, int):
                        value_to_append = value
                    elif value == [None]:
                        value_to_append = "NULL"
                    else:
                        extracted_value = list(value)[0]
                        extracted_value = re.sub("'", "''", str(extracted_value))
                        extracted_value = re.sub("\n", " ", str(extracted_value))
                        value_to_append = u"'{}'".format(extracted_value)
                else:
                    if field != "doi":
                        value_to_append = "NULL"
                    else:
                        break
                        print("error: doi can't be None")
                # Add it to a list
                values.append(value_to_append)
    return values

def delete_matching_from_db(parsed_articles):
    dois = [row["doi"] for row in parsed_articles]
    if not dois:
        return

    sql_command = u""
    for table_name in get_fields():
        sql_command += u"DELETE FROM {} WHERE doi in ({});".format(
            table_name, u",".join([u"'{}'".format(doi) for doi in dois]))
    Query_Executor().execute(sql_command)


def insert(table_name, fields, values_tot):
    values_tot_of_strings = []
    for value_list in values_tot:
        values_tot_of_strings.append('(' + ', '.join([str(x) for x in value_list]) + ')')

    sql_command = u"INSERT INTO {} ({}) VALUES {};".format(
        table_name, ', '.join(fields), ', '.join(values_tot_of_strings))
    # print(sql_command)
    Query_Executor().execute(sql_command)


def create_db_tables():
    """
    DATABASE CREATION
    """
    print('- ' * 30 + 'DATABASE CREATION')
    #  Timestamp
    start_time = time.time()

    #  db connexion

    urllib.parse.uses_netloc.append("postgres")
    url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

    connection = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    connection.autocommit = True

    cursor = connection.cursor()
    #~ cursor.execute('')
    #  Check if 'pubmed' db exists, if not, create it by executing SQL file line by line
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    local_tables = []
    for row in cursor:
        # print(row)
        local_tables.append(row[0])

    test_table_name = "doiboost_affiliation"  # last tablename
    if test_table_name in local_tables:
        print('Database already created')
    else:
        print('Database doesn\'t exist. Creation ..')
        for command in open("utils/database_creation_doiboost.sql", 'r'):
            if command != '\n' and not command.startswith('#'):
                cursor.execute(command)
        print('Database created')

    print('Elapsed time: {} sec for module: create_db_tables'.format(round(time.time() - start_time, 2)))
    cursor.close()
    connection.close()


# subset is needed by the pubmed library but not this one, at the moment
def get_file_list(subset=None):
    print('- ' * 30 + 'EXTRACTING FILES LIST FROM DOIBOOST')
    #  Timestamp
    start_time = time.time()

    #  Create directory to keep file during INSERT
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        inserted_log = open(insert_log_path, 'w')
        inserted_log.close()
    #  List of files to download
    gz_file_list = [u"part-00{0:03d}.gz".format(i) for i in range(0, 600+1)]
    # print(gz_file_list)
    print('{} files in the list'.format(len(gz_file_list)))
    print('Elapsed time: {} sec for module: get_file_list'.format(round(time.time() - start_time, 2)))

    return gz_file_list


def mark_as_started(file_name):

    q = """SELECT filename
            FROM  admin_inserted_files
            where filename = '{}' and started is not null""".format(file_name)

    #  Check if already INSERTED before
    rows_already_running = Query_Executor().select(q)
    if rows_already_running:
        return False  # not still available

    # add to inserted list
    Query_Executor().execute("insert into admin_inserted_files values ('{}', now(), NULL)".format(file_name))

    return True  # this filename is now in queue


def mark_as_finished(file_name):
    # add to inserted list
    Query_Executor().execute("update admin_inserted_files set finished=now() where filename='{}'".format(file_name))


def remove_downloaded_file(file_name):
    os.chdir(download_folder)
    try:
        os.remove('./' + file_name)
    except FileNotFoundError:
        print("tried to delete file {} but wasn't there".format(file_name))

def download(file_name):
    print('- ' * 30 + 'DOWNLOADING FILE ' + file_name)
    #  Timestamp
    start_time = time.time()

    #  Go to storage directory
    os.chdir(download_folder)

    full_url = u"https://s3-us-west-2.amazonaws.com/unpaywall-doiboost/doiBoost/{}".format(file_name)
    r = requests.get(full_url)
    print(full_url)
    print(r)
    open(file_name, 'wb').write(r.content)

    return file_name

def extract(file_name):
    print('- ' * 30 + 'FILE EXTRACTION')
    #  Timestamp
    start_time = time.time()
    os.chdir(download_folder)
    #  Extraction
    gz_file = gzip.open(file_name, 'rt', encoding='utf-8')
    file_content = gz_file.readlines()
    os.chdir(top_level_path)
    print('Elapsed time: {} sec for module: {}'.format(round(time.time() - start_time, 2), extract.__name__))

    return file_content

def parse(file_lines):
    print('- ' * 30 + 'XML FILE PARSING')
    #  Timestamp
    start_time = time.time()
    rows = []
    for string_row in file_lines:
        if string_row:
            try:
                # string_row = string_row.strip("\r\n")
                # string_row = string_row.strip("\"")
                rows += [eval(eval(string_row))]
            except ValueError:
                print("error on {}".format(string_row))
                raise
    print('Elapsed time: {} sec for module: {}'.format(round(time.time() - start_time, 2), parse.__name__))
    return rows

def build_insert_list(parsed_article, gz):
    start_time = time.time()

    # print(parsed_article)

    article_INSERT_list = []
    doi_primary_key = parsed_article["doi"]
    doi_primary_key = clean_doi(doi_primary_key)
    # print("doi_primary_key: {}".format(doi_primary_key))

    if not doi_primary_key:
        print("ERROR: NO DOI FOUND, return with empty article list")
        return []


    ''' - - - - - - - - - - - - - -
    doiboost_abstract
    - - - - - - - - - - - - - -  '''

    abstract_dicts = parsed_article["abstract"]
    for abstract_dict in abstract_dicts:
        if abstract_dict["provenance"] == "MAG":
            article_INSERT_list.append(
                {'name': 'doiboost_abstract',
                 'value': {'doi': [doi_primary_key],
                           'abstract': [abstract_dict["value"]],
                           'provenance': [abstract_dict["provenance"]]}
                 })


    # "doi" make sure is lower, normalized
    # "authors"  each one in its own row
    #   doi, author_order, given, family, fullname, orcid (schema==ORCID), all_identifiers jsonb
    #   "affiliations" each one a row if "provenance"==MAG
    #     doi, author_order, affiliation_order, value, official-page, grid_id, microsoft_id, wikipedia_id,
    # "abstract" value, provenance if provenance==MAG
    # "instances" if includes "microsoft.com"
    # collected-from

    # fields["doiboost_author"] = ['doi', 'author_order', 'given', 'family', 'fullname', 'orcid', 'mag_id']
    # fields["doiboost_affiliation"] = ['doi', 'author_order', 'affiliation_order', 'value', 'official_page', 'grid_id', 'microsoft_id', 'wikipedia_id']
    # return fields
    #

    # ''' - - - - - - - - - - - - - -
    # doiboost_author
    # - - - - - - - - - - - - - -  '''
    author_order = 0
    for author in parsed_article["authors"] or []:
        affiliation_order = 0
        for affiliation in author["affiliations"] or []:
            # this makes sure every affiliation is stored
            grid_id = None
            wikipedia_id = None
            microsoft_id = None
            for identifier in affiliation["identifiers"] or []:
                if identifier["schema"] == "grid.ac":
                    grid_id = identifier["value"]
                if identifier["schema"] == "wikpedia":  # need this typo
                    wikipedia_id = identifier["value"]
                if identifier["schema"] == "microsoftID":
                    microsoft_id = identifier["value"]

            article_INSERT_list.append({'name': 'doiboost_affiliation',
                 'value': {'doi': [doi_primary_key],
                           'author_order': author_order,
                           'affiliation_order': affiliation_order,
                           'value': [affiliation["value"]],
                           'official_page': [affiliation["official-page"]],
                           'grid_id': [grid_id],
                           'microsoft_id': [microsoft_id],
                           'wikipedia_id': [wikipedia_id]
                           }})
            affiliation_order += 1

        orcid = None
        mag_id = None
        for identifier in author["identifiers"] or []:
            if identifier["provenance"] == "MAG":
                mag_id = identifier["value"]
            if identifier["provenance"] == "ORCID":
                orcid = identifier["value"]

        article_INSERT_list.append(
            {'name': 'doiboost_author',
             'value': {'doi': [doi_primary_key],
                       'author_order': author_order,
                       'given': [author["given"]],
                       'family': [author["family"]],
                       'fullname': [author["fullname"]],
                       'orcid': [orcid],
                       'mag_id': [mag_id]
                       }
             })
        author_order += 1

    #  Final return, for every articles
    # print('Elapsed time: {} sec for module: {}'.format(round(time.time() - start_time, 2), build_insert_list.__name__))

    # import pprint
    # pprint.pprint(article_INSERT_list)

    return article_INSERT_list


def store_results(parsed_articles, file_to_download, file_downloaded, skip_existing):
    print('- ' * 30 + 'SQL INSERTION')

    #  Timestamp
    start_time_sql = time.time()

    #  Lists to create
    table_fields_lookup = get_fields()
    values = {}
    values_tot = {}
    for table_name in table_fields_lookup:
        values_tot[table_name] = []

    articles_count = 0
    insert_limit = 1000

    if skip_existing:
        print("not supported yet")
        return 1/0
    else:
        # Delete existing
        print("deleting existing")
        delete_matching_from_db(parsed_articles)
        articles_to_save = parsed_articles
        print("done deleting existing")

    # Create a dictionary with data to INSERT for every article
    for parsed_article in articles_to_save:

        #  Loading
        articles_count += 1
        if articles_count % 10000 == 0:
            print('{} articles inserted for file {}'.format(articles_count, file_to_download))

        article_INSERT_list = build_insert_list(parsed_article, gz=file_downloaded)

        # For every table in articles, loop to create global insert
        for insert_table in article_INSERT_list:
            for (table_name, fields) in table_fields_lookup.items():
                if insert_table['name'] == table_name:
                    values_this_item = get_values(table_name, fields, insert_table)
                    values_tot[table_name].append(values_this_item)

                    if (len(values_tot[table_name]) == insert_limit) or (articles_count == len(articles_to_save)):
                        insert(table_name, fields, values_tot[table_name])
                        values_tot[table_name] = []

    # Write the remaining entries
    for (table_name, fields) in table_fields_lookup.items():
        if len(values_tot[table_name]) > 0:
            insert(table_name, fields, values_tot[table_name])

    # then clear it all out
    for table_name in table_fields_lookup:
        values_tot[table_name] = []

    # remove file and add file_name to a list to ignore this file next time
    print(
        'Elapsed time: {} sec for module: {}'.format(round(time.time() - start_time_sql, 2), 'insert'))

    #  Flush RAM
    del parsed_articles
    del articles_to_save
    del values_tot

