import unicodedata
import re
from six import u as unicode
from six import string_types

class NoDoiException(Exception):
    pass

def remove_nonprinting_characters(unicode_input, encoding='utf-8'):
        # see http://www.fileformat.info/info/unicode/category/index.htm
    char_classes_to_remove = ["C", "M", "Z"]

    response = u''.join(c for c in unicode_input if unicodedata.category(c)[0] not in char_classes_to_remove)

    return response


def clean_doi(dirty_doi, return_none_if_error=False):
    if not dirty_doi:
        if return_none_if_error:
            return None
        else:
            raise NoDoiException("There's no DOI at all.")

    dirty_doi = dirty_doi.strip()
    dirty_doi = dirty_doi.lower()

    # test cases for this regex are at https://regex101.com/r/zS4hA0/1
    p = re.compile(u'(10\.\d+\/[^\s]+)')

    matches = re.findall(p, dirty_doi)
    if len(matches) == 0:
        if return_none_if_error:
            return None
        else:
            raise NoDoiException("There's no valid DOI.")

    match = matches[0]
    match = remove_nonprinting_characters(match)

    try:
        resp = unicode(match, "utf-8")  # unicode is valid in dois
    except (TypeError, UnicodeDecodeError):
        resp = match

    # remove any url fragments
    if u"#" in resp:
        resp = resp.split(u"#")[0]

    # remove double quotes, they shouldn't be there as per http://www.doi.org/syntax.html
    resp = resp.replace('"', '')

    # remove trailing period, comma -- it is likely from a sentence or citation
    if resp.endswith(u",") or resp.endswith(u"."):
        resp = resp[:-1]

    return resp