import requests
import os
import re
import sys
import time
import configparser
import pubmed
import doiboost

# do a single test on a locally downloaded file
# filename = "/Users/hpiwowar/Downloads/pubmed18n0885.xml"
# with open(filename, "r") as fp:
#     file_content = fp.read()

# or get one from pubmed
# pmid = 29456894
# r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={}&WebEnv=123&rettype=xml&retmode=xml".format(
#     pmid))
# file_content = r.content
# articles = pubmed.parse(file_content)
# pubmed.store_results(articles, file_to_download=None, file_downloaded=None)

# file_to_download_name = "download_cache/part-00065.gz"
# this_file_path = os.path.dirname(os.path.realpath(__file__))
# file_to_download = os.path.join(this_file_path, file_to_download_name)
#
# file_downloaded = None
# file_content = doiboost.extract(file_name=file_to_download)
# # parse XML file to extract articles
# parsed_articles = doiboost.parse(file_content)
# # store the results in the DB
# doiboost.store_results(parsed_articles, file_to_download, file_downloaded)

articles = [
    {'publisher': None, 'issn': [{'type': 'print', 'value': '0008-543X'}, {'type': 'electronic', 'value': '1097-0142'}], 'doi': '10.1002/1097-0142(20010715)92:2<232::aid-cncr1314>3.0.co;2-g', 'license': [{'url': 'http://doi.wiley.com/10.1002/tdm_license_1.1', 'content-version': 'tdm', '"delay-in-days': None, 'date-time': '2015-09-01T00:00:00Z'}], 'published-print': '2001-7-15', 'title': ['Prediction of chemotherapeutic response by technetium 99m-MIBI scintigraphy in breast carcinoma patients'], 'issued': '2001-1-1', 'abstract': [{'provenance': 'MAG', 'value': 'BACKGROUND\r\n\r\nSignificance of Technetium 99m (99mTc)â\x80\x93MIBI scintigraphy in the prediction of response to anthracylines and taxanes (both are substrates for P-glycoprotein [P-gp]) as well as relation between 99mTc-MIBI uptake and P-gp or MDR1 mRNA expression in tumors were studied in patients with breast carcinoma.\r\n\r\n\r\n\r\nMETHODS\r\n\r\nForty-six female patients with locally advanced (n = 15) or metastatic (n = 31) breast carcinoma were recruited in this study. Before chemotherapy (epirubicin and cyclophosphamide [n = 20] or decetaxel [n = 26]), 99mTc-MIBI scintigraphy was performed to obtain the T/N (tumor to normal tissue) ratios of 99mTc-MIBI uptake at 10 minutes (T/N[e]) and at 180 minutes (T/N[d]) after the 99mTc-MIBI injection. Expression of MDR1 mRNA and P-gp in tumors (n = 32) were determined by a quantitative real-time polymerase chain reaction and immunohistochemistry, respectively.\r\n\r\n\r\n\r\nRESULTS\r\n\r\nClinical significance of T/N(e) and T/N(d) ratios in the prediction of chemotherapeutic response was evaluated using the arbitrary cutoff values of 3.0 for T/N(e) ratios and 2.0 for T/N(d) ratios. Positive predictive value, negative predictive value, and diagnostic accuracy of T/N(d) ratios (81.0%, 96.0%, and 89.1%, respectively) were higher, although statistically not significant, than those of T/N(e) ratios (73.3%, 77.4%, and 76.1%, respectively), and these values were not affected by type of chemotherapy. MDR1 mRNA levels were not significantly different between the lesions with high (â\x89¥ 2.0) and low (\\u003c 2.0) T/N(d) ratios, but P-gp expression was significantly (P \\u003c 0.01) higher in the lesions with low T/N(d) ratios than in those with high T/N(d) ratios.\r\n\r\n\r\n\r\nCONCLUSIONS\r\n\r\nT/N(d) ratios determined by 99mTc-MIBI scintigraphy are useful in the prediction of response to chemotherapy with epirubicin and cyclophosphamide or docetaxel as well as in the in vivo evaluation of P-gp expression status in tumors in patients with locally advanced or recurrent breast carcinoma. Cancer 2001;92:232â\x80\x939. Â© 2001 American Cancer Society.'}], 'doi-url': 'http://dx.doi.org/10.1002/1097-0142(20010715)92:2<232::aid-cncr1314>3.0.co;2-g', 'instances': [{'url': 'https://api.wiley.com/onlinelibrary/tdm/v1/articles/10.1002%2F1097-0142(20010715)92:2%3C232::AID-CNCR1314%3E3.0.CO;2-G', 'provenance': 'CrossRef', 'access-rights': 'UNKNOWN'}], 'authors': [{'affiliations': [{'official-page': 'http://www.osaka-u.ac.jp/en/index.html', 'provenance': 'MAG', 'identifiers': [{'value': 'http://en.wikipedia.org/wiki/Osaka_University', 'schema': 'wikpedia'}, {'value': 'grid.136593.b', 'schema': 'grid.ac'}], 'value': 'Osaka University'}], 'given': 'Yuuki', 'identifiers': [{'provenance': 'MAG', 'value': 'https://academic.microsoft.com/#/detail/2167107913', 'schema': 'URL'}], 'fullname': 'Yuuki Takamura', 'family': 'Takamura'}, {'affiliations': [{'official-page': 'http://www.osaka-u.ac.jp/en/index.html', 'provenance': 'MAG', 'identifiers': [{'value': 'http://en.wikipedia.org/wiki/Osaka_University', 'schema': 'wikpedia'}, {'value': 'grid.136593.b', 'schema': 'grid.ac'}], 'value': 'Osaka University'}], 'given': 'Yasuo', 'identifiers': [{'provenance': 'MAG', 'value': 'https://academic.microsoft.com/#/detail/2026670621', 'schema': 'URL'}], 'fullname': 'Yasuo Miyoshi', 'family': 'Miyoshi'}, {'affiliations': [{'official-page': 'http://www.osaka-u.ac.jp/en/index.html', 'provenance': 'MAG', 'identifiers': [{'value': 'http://en.wikipedia.org/wiki/Osaka_University', 'schema': 'wikpedia'}, {'value': 'grid.136593.b', 'schema': 'grid.ac'}], 'value': 'Osaka University'}], 'given': 'Tetsuya', 'identifiers': [{'provenance': 'MAG', 'value': 'https://academic.microsoft.com/#/detail/2250767522', 'schema': 'URL'}], 'fullname': 'Tetsuya Taguchi', 'family': 'Taguchi'}, {'affiliations': [{'official-page': 'http://www.osaka-u.ac.jp/en/index.html', 'provenance': 'MAG', 'identifiers': [{'value': 'http://en.wikipedia.org/wiki/Osaka_University', 'schema': 'wikpedia'}, {'value': 'grid.136593.b', 'schema': 'grid.ac'}], 'value': 'Osaka University'}], 'given': 'Shinzaburo', 'identifiers': [{'provenance': 'MAG', 'value': 'https://academic.microsoft.com/#/detail/2097188688', 'schema': 'URL'}], 'fullname': 'Shinzaburo Noguchi', 'family': 'Noguchi'}], 'collectedFrom': ['CrossRef', 'MAG'], 'accepted': None, 'type': 'journal-article', 'published-online': '2001-1-1', 'subject': ['Cancer Research', 'Oncology']}
    ]
doiboost.store_results(articles, file_to_download=None, file_downloaded=None)

