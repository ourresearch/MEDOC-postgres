import requests
import os
import re
import sys
import time
import configparser

sys.path.append('./lib')
import MEDOC
import getters

from __medoc__ import store_results

MEDOC = MEDOC.MEDOC()
parameters = configparser.ConfigParser()
parameters.read('./configuration.cfg')

# do a single test on a locally downloaded file
# filename = "/Users/hpiwowar/Downloads/pubmed18n0885.xml"
# with open(filename, "r") as fp:
#     file_content = fp.read()

# or get one from pubmed
pmid = 18700873
r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={}&WebEnv=123&rettype=xml&retmode=xml".format(
    pmid))
file_content = r.content
articles = MEDOC.parse(data=file_content)
store_results(MEDOC, articles, parameters, file_to_download=None, file_downloaded=None)

