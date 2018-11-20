
#==============================================================
# TABLE: doiboost_abstract
#==============================================================
CREATE TABLE doiboost_abstract (doi TEXT NOT NULL, abstract TEXT, provenance TEXT);
CREATE INDEX doiboost_abstract_doi_idx on doiboost_abstract(doi);

#==============================================================
# TABLE: doiboost_author
#==============================================================
CREATE TABLE doiboost_author (doi TEXT NOT NULL, author_order NUMERIC, given TEXT, family TEXT, fullname TEXT, orcid TEXT, mag_id TEXT);
CREATE INDEX doiboost_author_doi_idx on doiboost_author(doi);

#==============================================================
# TABLE: doiboost_affiliation
#==============================================================
CREATE TABLE doiboost_affiliation (doi TEXT NOT NULL, author_order NUMERIC, affiliation_order NUMERIC, value TEXT, official_page TEXT, grid_id TEXT, microsoft_id TEXT, wikipedia_id TEXT);
CREATE INDEX doiboost_affiliation_doi_idx on doiboost_affiliation(doi);
