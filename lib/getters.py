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


import sys
import re
from lib.sql_helper import Query_Executor


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
    fields["medline_article_language"] = ['pmid', 'language']
    fields["medline_article_publication_type"] = ['pmid', 'publication_type']
    fields["medline_author"] = ['pmid', 'last_name', 'fore_name', 'first_name', 'middle_name', 'initials', 'suffix',
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
                try:
                    # Get "VALUE"
                    value_to_append = "'" + (list(value)[0]).replace("'", '') + "'"
                except:
                    if field != "pmid":
                        value_to_append = "'N/A'"
                    else:
                        break
                        print("error: pmid can't be N/A")
                # Add it to a list
                values.append(value_to_append)
    return values

def delete_existing(article, parameters):
    pmids = re.findall('<articleid idtype="pubmed">([0-9]*)</articleid>', str(article))
    if not pmids:
        return

    sql_command = u""
    for table_name in get_fields():
        sql_command += u"DELETE FROM {} WHERE pmid in ({});".format(
            table_name, u",".join(pmids))
    Query_Executor(parameters).execute(sql_command)


def insert(table_name, fields, values_tot, parameters):
    values_tot_of_strings = []
    for value_list in values_tot:
        values_tot_of_strings.append('(' + ', '.join(value_list) + ')')

    sql_command = u"INSERT INTO {} ({}) VALUES {};".format(
        table_name, ', '.join(fields), ', '.join(values_tot_of_strings))
    # print(sql_command)
    Query_Executor(parameters).execute(sql_command)

