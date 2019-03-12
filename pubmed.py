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

regex_gz_html = '"(pubmed.*.xml.gz)"'

this_file_path = os.path.dirname(os.path.realpath(__file__))
top_level_path = this_file_path  # depends on where this file is in hierarchy

insert_log_path = os.path.join(top_level_path, "log/inserted.log")
download_folder = os.path.join(top_level_path, "download_cache/")

def get_fields():
    fields = {}
    # pmid always first
    fields["medline_citation"] = ['pmid', 'date_completed', 'pub_date_day', 'citation_owner', 'iso_abbreviation', 'article_title',
                                   'volume', 'vernacular_title', 'pub_date_year', 'date_revised',
                                   'date_of_electronic_publication', 'article_author_list_comp_yn', 'medline_pgn',
                                   'date_created', 'country', 'xml_file_name', 'medline_date', 'number_of_references',
                                   'data_bank_list_comp_yn', 'nlm_unique_id', 'abstract_text', 'citation_status',
                                   'grantlist_complete_yn', 'copyright_info', 'issue', 'journal_title', 'issn',
                                   'pub_date_month', 'medline_ta']
    fields["medline_raw_xml"] = ['pmid', 'raw_xml', 'updated']
    fields["medline_article_language"] = ['pmid', 'language']
    fields["medline_article_publication_type"] = ['pmid', 'publication_type']
    fields["medline_affiliation"] = ['pmid', 'author_order', 'affiliation_order', 'affiliation']
    fields["medline_author"] = ['pmid', 'author_order', 'last_name', 'fore_name', 'first_name', 'middle_name', 'initials', 'suffix',
                             'affiliation', 'collective_name', 'orcid']
    fields["medline_chemical_list"] = ['pmid', 'registry_number', 'name_of_substance']
    fields["medline_citation_other_id"] = ['pmid', 'source', 'other_id']
    fields["medline_citation_subsets"] = ['pmid', 'citation_subset']
    fields["medline_comments_corrections"] = ['pmid', 'ref_pmid', 'type', 'ref_source']
    fields["medline_data_bank"] = ['pmid', 'accession_number']
    fields["medline_grant"] = ['pmid', 'grant_id', 'acronym', 'agency', 'country']
    fields["medline_investigator"] = ['pmid', 'last_name', 'fore_name', 'first_name', 'middle_name', 'initials', 'suffix',
                                   'affiliation', 'orcid']
    fields["medline_mesh_heading"] = ['pmid', 'descriptor_name', 'descriptor_ui', 'descriptor_name_major_yn',
                                   'qualifier_name', 'qualifier_ui', 'qualifier_name_major_yn']
    fields["medline_personal_name_subject"] = ['pmid', 'last_name', 'fore_name', 'first_name', 'middle_name', 'initials',
                                            'suffix', 'orcid']
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
                        value_to_append = u"'{}'".format(extracted_value)
                else:
                    if field != "pmid":
                        value_to_append = "NULL"
                    else:
                        break
                        print("error: pmid can't be None")
                # Add it to a list
                values.append(value_to_append)
    return values

def delete_existing(raw_articles):
    pmids = []
    for raw_article in raw_articles:
        pmids += re.findall('<articleid idtype="pubmed">([0-9]*)</articleid>', str(raw_article), re.IGNORECASE)
    if not pmids:
        return

    sql_command = u""
    for table_name in get_fields():
        sql_command += u"DELETE FROM {} WHERE pmid in ({});".format(
            table_name, u",".join(pmids))
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

    test_table_name = "medline_investigator"  # last tablename
    if test_table_name in local_tables:
        print('Database already created')
    else:
        print('Database doesn\'t exist. Creation ..')
        for command in open("utils/database_creation_pubmed.sql", 'r'):
            if command != '\n' and not command.startswith('#'):
                cursor.execute(command)
        print('Database created')

    print('Elapsed time: {} sec for module: create_db_tables'.format(round(time.time() - start_time, 2)))
    cursor.close()
    connection.close()


def get_file_list():
    print('- ' * 30 + 'EXTRACTING FILES LIST FROM PUBMED')
    #  Timestamp
    start_time = time.time()

    #  Create directory to keep file during INSERT
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        inserted_log = open(insert_log_path, 'w')
        inserted_log.close()
    #  List of files to download
    gz_file_list = []


    url = "https://ftp.ncbi.nlm.nih.gov"

    # #  BASELINE
    # r = requests.get(url + "/pubmed/baseline/")
    # page = r.text
    # matches = re.findall(regex_gz_html, page)
    # for file_name in matches:
    #     gz_file_list.append('baseline/' + file_name)

    #  UPDATES
    r = requests.get(url + "/pubmed/updatefiles/")
    page = r.text
    matches = re.findall(regex_gz_html, page)
    for file_name in matches:
        gz_file_list.append('updatefiles/' + file_name)

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
    file_name = re.findall('(.*)/(.*)', file_name)[0][1]
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

    file_name_dir = re.findall('(.*)/(.*)', file_name)
    url = "https://ftp.ncbi.nlm.nih.gov"
    full_url = url + "/pubmed/" + file_name
    r = requests.get(full_url)
    open(file_name_dir[0][1], 'wb').write(r.content)

    return file_name_dir[0][1]

def extract(file_name):
    print('- ' * 30 + 'FILE EXTRACTION')
    #  Timestamp
    start_time = time.time()
    os.chdir(download_folder)
    #  Extraction
    file_name_dir = re.findall('(.*)/(.*)', file_name)
    gz_file = gzip.open(file_name_dir[0][1], 'rt', encoding='utf-8')
    file_content = gz_file.read()
    os.chdir(top_level_path)
    print('Elapsed time: {} sec for module: {}'.format(round(time.time() - start_time, 2), extract.__name__))

    return file_content

def parse(data):
    print('- ' * 30 + 'XML FILE PARSING')
    #  Timestamp
    start_time = time.time()
    #  Souping

    # data = "<PubmedArticle>\n" + data.split("<PubmedArticle>")[1]
    # print(data)

    articles = re.findall(r"<PubmedArticle>(.*?)</PubmedArticle>", data, re.MULTILINE|re.DOTALL)
    # articles = articles[0:5]

    # soup = BeautifulSoup(data, 'lxml')
    # articles = soup.find_all('pubmedarticle')
    # articles = soup

    print('Elapsed time: {} sec for module: {}'.format(round(time.time() - start_time, 2), parse.__name__))
    # print(articles)

    return articles

def build_insert_list(article_raw, gz):
    start_time = time.time()

    soup_article = BeautifulSoup(str(article_raw), 'lxml')
    article_INSERT_list = []
    pmid_primary_key = re.findall('<articleid idtype="pubmed">([0-9]*)</articleid>', str(soup_article))
    # print("pmid_primary_key: {}".format(pmid_primary_key))

    if not pmid_primary_key:
        # example that needs this hack:  pmid 27443694
        # print("DID NOT FIND pmid_primary_key THE NORMAL WAY")
        pmid_primary_key = re.findall('<medlinecitation [A-Za-z-=\" ]*>\s*<pmid version=\"\d\">(\d*)</pmid>', str(soup_article), re.DOTALL | re.MULTILINE)
        # print("FOUND pmid_primary_key THE OTHER WAY: {}".format(pmid_primary_key))

    if not pmid_primary_key:
        print("ERROR: NO PMID FOUND, return with empty article list")
        return []

    #  Regexs
    r_year = re.compile('<year>([0-9]{4})</year>')
    r_month = re.compile('<month>([0-9]{2})</month>')
    r_day = re.compile('<day>([0-9]{2})</day>')

    ''' - - - - - - - - - - - - - -  
    medline_citation
    - - - - - - - - - - - - - -  '''
    #  date_created
    date_created = soup_article.find_all('datecreated')
    try:
        date_completed_value = [
            re.findall(r_year, str(date_created))[0] + '-' + re.findall(r_month, str(date_created))[0] + '-' +
            re.findall(r_day, str(date_created))[0]]
    except:
        date_completed_value = ['1900-01-01']
    #  date_completed
    date_completed = soup_article.find_all('datecompleted')
    try:
        date_completed_value = [
            re.findall(r_year, str(date_completed))[0] + '-' + re.findall(r_month, str(date_completed))[0] + '-' +
            re.findall(r_day, str(date_completed))[0]]
    except:
        date_completed_value = ['1900-01-01']
    #  date_revised
    date_revised = soup_article.find_all('daterevised')
    try:
        date_revised_value = [
            re.findall(r_year, str(date_revised))[0] + '-' + re.findall(r_month, str(date_revised))[0] + '-' +
            re.findall(r_day, str(date_revised))[0]]
    except:
        date_revised_value = ['1900-01-01']
    #  date_published
    date_published = soup_article.find_all('pubdate')
    #  journal
    journal = soup_article.find_all('journal')
    #  abstract_text_list
    abstract_text_list = re.findall('<abstracttext.*?>(.*?)</abstracttext>', str(soup_article))
    # if is a long list it is because it is a structured abstract, see https://www.ncbi.nlm.nih.gov/pubmed/16476868?report=xml&format=text
    if len(abstract_text_list) > 1:
        abstract_text_raw = ""
        abstract_text_list_with_attributes = re.findall('<abstracttext(.*?)>(.*?)</abstracttext>', str(soup_article))
        for (abstract_text_attributes, abstract_text_inner) in abstract_text_list_with_attributes:
            abstract_text_labels = re.findall('label=\"(.*?)\"', abstract_text_attributes)
            if abstract_text_labels:
                abstract_text_raw += u"{}: ".format(abstract_text_labels[0])
            abstract_text_raw += u"{} ".format(abstract_text_inner)
        abstract_text = re.sub('\"', ' ', str(abstract_text_raw))
        abstract_text = [abstract_text]  # is expected to be a list
    else:
        abstract_text = abstract_text_list

    #  date_of_electronic_publication
    date_of_electronic_publication = soup_article.find_all('articledate', attrs={'datetype': 'Electronic'})
    try:
        date_of_electronic_publication_value = [re.findall(r_year, str(date_of_electronic_publication))[0] + '-' +
                                                re.findall(r_month, str(date_of_electronic_publication))[0] + '-' +
                                                re.findall(r_day, str(date_of_electronic_publication))[0]]
    except:
        date_of_electronic_publication_value = ['1900-01-01']
    #  MEDLINE infos
    medline_info_journal = soup_article.find_all('medlinejournalinfo')
    #  INSERT
    article_INSERT_list.append(
        {'name': 'medline_citation',
         'value': {
             'pmid': pmid_primary_key,
             'date_created': date_completed_value,
             'date_completed': date_completed_value,
             'date_revised': date_revised_value,
             'issn': re.findall('<issn issntype=".*">(.*)</issn>', str(soup_article)),
             'volume': re.findall('<volume>([0-9]*)</volume>', str(soup_article)),
             'issue': re.findall('<issue>([0-9]*)</issue>', str(soup_article)),
             'pub_date_year': re.findall('<year>([0-9]{4})</year>', str(date_published)),
             'pub_date_month': re.findall('<month>([0-9]{2}|\w+)</month>', str(date_published)),
             'pub_date_day': re.findall('<day>([0-9]{2})</day>', str(date_published)),
             'medline_date': re.findall('<medlinedate>(.*)</medlinedate>', str(date_published)),
             'journal_title': re.findall('<title>(.*)</title>', str(journal)),
             'iso_abbreviation': re.findall('<isoabbreviation>(.*)</isoabbreviation>', str(journal)),
             'article_title': re.findall('<articletitle>(.*)</articletitle>', str(soup_article)),
             'medline_pgn': re.findall('<medlinepgn>(.*)</medlinepgn>', str(soup_article)),
             'abstract_text': abstract_text,
             'copyright_info': re.findall('<copyrightinformation>(.*)</copyrightinformation>', str(soup_article)),
             'article_author_list_comp_yn': re.findall('<authorlist completeyn="([A-Z]{1})">', str(soup_article)),
             'data_bank_list_comp_yn': re.findall('<databanklist completeyn="([A-Z]{1})">', str(soup_article)),
             'grantlist_complete_yn': re.findall('<grantlist completeyn="([A-Z]{1})">', str(soup_article)),
             'vernacular_title': re.findall('<vernaculartitle>(.*)</vernaculartitle>', str(soup_article)),
             'date_of_electronic_publication': date_of_electronic_publication_value,
             'country': re.findall('<country>(.*)</country>', str(medline_info_journal)),
             'medline_ta': re.findall('<medlineta>(.*)</medlineta>', str(soup_article)),
             'nlm_unique_id': re.findall('<nlmuniqueid>(.*)</nlmuniqueid>', str(soup_article)),
             'xml_file_name': gz,
             'number_of_references': re.findall('<numberofreferences>(.*)</numberofreferences>', str(soup_article)),
             'citation_owner': re.findall('<medlinecitation .*?owner="(.*?)".*?>', str(soup_article)),
             'citation_status': re.findall('<medlinecitation .*?status="([A-Za-z])".*?>', str(soup_article))}
         }
    )

    ''' - - - - - - - - - - - - - -
    medline_raw_xml
    - - - - - - - - - - - - - -  '''
    article_INSERT_list.append(
        {'name': 'medline_raw_xml',
         'value': {'pmid': pmid_primary_key,
                   'raw_xml': [str(article_raw)],
                   'updated': [datetime.datetime.utcnow().isoformat()]}
         })

    ''' - - - - - - - - - - - - - -
    medline_article_language
    - - - - - - - - - - - - - -  '''
    languages_list = soup_article.find_all('language')
    for language in languages_list:
        article_INSERT_list.append(
            {'name': 'medline_article_language',
             'value': {'pmid': pmid_primary_key,
                       'language': re.findall('<language>(.*)</language>', str(language))}
             })

    ''' - - - - - - - - - - - - - -
    medline_article_publication_type
    - - - - - - - - - - - - - -  '''
    publication_type_list = soup_article.find_all('publicationtype')
    for publication_type in publication_type_list:
        article_INSERT_list.append(
            {'name': 'medline_article_publication_type',
             'value': {'pmid': pmid_primary_key,
                       'publication_type': re.findall('<publicationtype ui=".*?">(.*?)</publicationtype>',
                                                      str(publication_type))}
             })

    ''' - - - - - - - - - - - - - -
    medline_author
    - - - - - - - - - - - - - -  '''
    author_list = soup_article.find_all('author')
    author_order = 0
    for author in author_list:
        all_affiliations = re.findall('<affiliation>(.*)</affiliation>', str(author))
        affiliation_order = 0
        for affiliation in all_affiliations:
            # this makes sure every affiliation is stored
            article_INSERT_list.append({'name': 'medline_affiliation',
                 'value': {'pmid': pmid_primary_key,
                           'author_order': author_order,
                           'affiliation_order': affiliation_order,
                           'affiliation': [affiliation]
                           }})
            affiliation_order += 1
        article_INSERT_list.append(
            {'name': 'medline_author',
             'value': {'pmid': pmid_primary_key,
                       'author_order': author_order,
                       'last_name': re.findall('<lastname>(.*)</lastname>', str(author)),
                       'fore_name': re.findall('<forename>(.*)</forename>', str(author)),
                       'first_name': re.findall('<firstname>(.*)</firstname>', str(author)),
                       'middle_name': re.findall('<middlename>(.*)</middlename>', str(author)),
                       'initials': re.findall('<initials>(.*)</initials>', str(author)),
                       'suffix': re.findall('<suffix>(.*)</suffix>', str(author)),
                       'affiliation': all_affiliations, # only the first one will be inserted by insert functino
                       'collective_name': re.findall('<collectivename>(.*)</collectivename>', str(author)),
                       'orcid': re.findall('<identifier source="ORCID">(.*)</identifier>', str(author))
                       }
             })
        author_order += 1

    ''' - - - - - - - - - - - - - -  
    medline_chemical_list
    - - - - - - - - - - - - - -  '''
    chemical_list = soup_article.find_all('chemical')
    for chemical in chemical_list:
        article_INSERT_list.append(
            {'name': 'medline_chemical_list',
             'value': {'pmid': pmid_primary_key,
                       'registry_number': re.findall('<registrynumber>(.*)</registrynumber>', str(chemical)),
                       'name_of_substance': re.findall('<nameofsubstance ui=".*">(.*)</nameofsubstance>',
                                                       str(chemical))}
             })

    ''' - - - - - - - - - - - - - - 
    medline_citation_other_id
    - - - - - - - - - - - - - - '''
    other_ids_list = soup_article.find_all('otherid')
    for other_id in other_ids_list:
        article_INSERT_list.append(
            {'name': 'medline_citation_other_id',
             'value': {'pmid': pmid_primary_key,
                       'source': re.findall('<otherid source="(.*)">.*</otherid>', str(other_id)),
                       'other_id': re.findall('<otherid source=".*">(.*)</otherid>', str(other_id))}
             })

    # other ids are also called "articleid"
    other_ids_list = soup_article.find_all('articleid')
    for other_id in other_ids_list:
        article_INSERT_list.append(
            {'name': 'medline_citation_other_id',
             'value': {'pmid': pmid_primary_key,
                       'source': re.findall('<articleid idtype="(.*)">.*</articleid>', str(other_id)),
                       'other_id': re.findall('<articleid idtype=".*">(.*)</articleid>', str(other_id))}
             })

    ''' - - - - - - - - - - - - - - 
    medline_citation_subsets
    - - - - - - - - - - - - - - '''
    citation_subsets_list = soup_article.find_all('citationsubset')
    for citation_subsets in citation_subsets_list:
        article_INSERT_list.append(
            {'name': 'medline_citation_subsets',
             'value': {'pmid': pmid_primary_key,
                       'citation_subset': re.findall('<citationsubset>(.*)</citationsubset>',
                                                     str(citation_subsets))}
             })

    ''' - - - - - - - - - - - - - - 
    medline_comments_corrections
    - - - - - - - - - - - - - - '''
    medline_comments_corrections_list = soup_article.find_all('commentscorrections')
    for comment in medline_comments_corrections_list:
        article_INSERT_list.append(
            {'name': 'medline_comments_corrections',
             'value': {'pmid': pmid_primary_key,
                       'ref_pmid': re.findall('<pmid version="1">(\d+)</pmid>', str(comment)),
                       'type': re.findall('<commentscorrections reftype="(.*?)">', str(comment)),
                       'ref_source': re.findall('<refsource>(.*)</refsource>', str(comment))}
             })

    ''' - - - - - - - - - - - - - - 
    medline_data_bank
    - - - - - - - - - - - - - - '''
    medline_data_bank_list = soup_article.find_all('accessionnumber')
    for databank in medline_data_bank_list:
        article_INSERT_list.append(
            {'name': 'medline_data_bank',
             'value': {'pmid': pmid_primary_key,
                       'accession_number': re.findall('<accessionnumber>(.*)</accessionnumber>', str(databank))}
             })

    ''' - - - - - - - - - - - - - - 	
    medline_grant
    - - - - - - - - - - - - - - '''
    medline_grant_list = soup_article.find_all('grant')
    for grant in medline_grant_list:
        article_INSERT_list.append(
            {'name': 'medline_grant',
             'value': {'pmid': pmid_primary_key,
                       'grant_id': re.findall('<grantid>(.*)</grantid>', str(grant)),
                       'acronym': re.findall('<acronym>(.*)</acronym>', str(grant)),
                       'agency': re.findall('<agency>(.*)</agency>', str(grant)),
                       'country': re.findall('<country>(.*)</country>', str(grant))}
             })

    ''' - - - - - - - - - - - - - - 	
    medline_investigator
    - - - - - - - - - - - - - - '''
    medline_investigator_list = soup_article.find_all('investigator')
    for investigator in medline_investigator_list:
        article_INSERT_list.append(
            {'name': 'medline_investigator',
             'value': {'pmid': pmid_primary_key,
                       'last_name': re.findall('<lastname>(.*)</lastname>', str(investigator)),
                       'fore_name': re.findall('<forename>(.*)</forename>', str(investigator)),
                       'first_name': re.findall('<firstname>(.*)</firstname>', str(investigator)),
                       'middle_name': re.findall('<middlename>(.*)</middlename>', str(investigator)),
                       'initials': re.findall('<initials>(.*)</initials>', str(investigator)),
                       'suffix': re.findall('<suffix>(.*)</suffix>', str(investigator)),
                       'affiliation': re.findall('<affiliation>(.*)</affiliation>', str(investigator)),
                       'orcid': re.findall('<identifier source="ORCID">(.*)</identifier>', str(investigator))
                       }
             })

    ''' - - - - - - - - - - - - - - 
    medline_mesh_heading
    - - - - - - - - - - - - - - '''
    medline_mesh_heading_list = soup_article.find_all('meshheading')
    for mesh in medline_mesh_heading_list:
        article_INSERT_list.append(
            {'name': 'medline_mesh_heading',
             'value': {'pmid': pmid_primary_key,
                       'descriptor_name': re.findall(
                           '<descriptorname .*majortopicyn="[A-Z]{1}".*?>(.*?)</descriptorname>', str(mesh)),

                       'descriptor_ui': re.findall(
                           '<descriptorname .*?ui="(D\d+)".*?>.*?</descriptorname>', str(mesh)),

                       'descriptor_name_major_yn': re.findall(
                           '<descriptorname .*?majortopicyn="([A-Z]{1})".*?>.*?</descriptorname>', str(mesh)),
                       'qualifier_name': re.findall(
                           '<qualifiername .*?>(.*?)</qualifiername>', str(mesh)),

                       'qualifier_ui': re.findall(
                           '<qualifiername .*?ui="(Q\d+)">.*?</qualifiername>',
                           str(mesh)),

                       'qualifier_name_major_yn': re.findall(
                           '<qualifiername .*?majortopicyn="([A-Z]{1})".*?>.*?</qualifiername>', str(mesh))
                       }
             })

    ''' - - - - - - - - - - - - - - 
    medline_personal_name_subject
    - - - - - - - - - - - - - - '''
    medline_personal_name_subject_list = soup_article.find_all('personalnamesubject')
    for subject in medline_personal_name_subject_list:
        article_INSERT_list.append(
            {'name': 'medline_personal_name_subject',
             'value': {'pmid': pmid_primary_key,
                       'last_name': re.findall('<lastname>(.*)</lastname>', str(subject)),
                       'fore_name': re.findall('<forename>(.*)</forename>', str(subject)),
                       'first_name': re.findall('<firstname>(.*)</firstname>', str(subject)),
                       'middle_name': re.findall('<middlename>(.*)</middlename>', str(subject)),
                       'initials': re.findall('<initials>(.*)</initials>', str(subject)),
                       'suffix': re.findall('<suffix>(.*)</suffix>', str(subject)),
                       'orcid': re.findall('<identifier source="ORCID">(.*)</identifier>', str(subject))
                       }
             })

    #  Final return, for every articles
    # print('Elapsed time: {} sec for module: {}'.format(round(time.time() - start_time, 2), build_insert_list.__name__))
    # print(article_INSERT_list)

    return article_INSERT_list


def store_results(raw_articles, file_to_download, file_downloaded):
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

    # Delete existing
    print("deleting existing")
    delete_existing(raw_articles)
    print("done deleting existing")

    # Create a dictionary with data to INSERT for every article
    for raw_article in raw_articles:

        #  Loading
        articles_count += 1
        if articles_count % 10000 == 0:
            print('{} articles inserted for file {}'.format(articles_count, file_to_download))

        article_cleaned = re.sub("'", "''", str(raw_article))
        article_INSERT_list = build_insert_list(article_cleaned, gz=file_downloaded)

        # For every table in articles, loop to create global insert
        for insert_table in article_INSERT_list:
            for (table_name, fields) in table_fields_lookup.items():
                if insert_table['name'] == table_name:
                    values_this_item = get_values(table_name, fields, insert_table)
                    values_tot[table_name].append(values_this_item)

                    if (len(values_tot[table_name]) == insert_limit) or (articles_count == len(raw_articles)):
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
    del raw_articles
    del values_tot
