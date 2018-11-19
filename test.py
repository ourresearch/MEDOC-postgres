import requests
import os
import re
import sys
import time
import configparser
import pubmed

# do a single test on a locally downloaded file
# filename = "/Users/hpiwowar/Downloads/pubmed18n0885.xml"
# with open(filename, "r") as fp:
#     file_content = fp.read()

# or get one from pubmed
pmid = 29456894
r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={}&WebEnv=123&rettype=xml&retmode=xml".format(
    pmid))
file_content = r.content
articles = pubmed.parse(data=file_content)
pubmed.store_results(articles, file_to_download=None, file_downloaded=None)

