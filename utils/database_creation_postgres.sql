
# 			relational db MEDLINE Schema

# Development:
# 	Gaurav Bhalotia (Feb. 16, 2003)
# 	Ariel Schwartz (Jun. 10, 2003)
#		Emeric Dynomant (Jun. 08, 2017)
#   Heather Piwowar (Aug. 20, 2018) port to postgres

# Based on: 
# 	nlmmedline_021101.dtd
#		nlmmedlinecitation_021101.dtd 
#		nlmcommon_021101.dtd 

# The FTP are located at: 
#		ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/

# Script to fill it available on github:
#		mysql original: https://github.com/MrMimic/MEDOC
#   postgres port: https://github.com/impactstory/MEDOC-postgres


#==============================================================
# TABLE: medline_citation 
#==============================================================
CREATE TABLE medline_citation (pmid INTEGER NOT NULL, date_created TIMESTAMP NOT NULL, date_completed TIMESTAMP, date_revised TIMESTAMP, issn TEXT, volume TEXT, issue TEXT, pub_date_year TEXT, pub_date_month TEXT, pub_date_day TEXT, medline_date TEXT, journal_title TEXT, iso_abbreviation TEXT, article_title TEXT NOT NULL, medline_pgn TEXT, abstract_text TEXT, copyright_info TEXT, article_author_list_comp_yn TEXT DEFAULT 'Y', data_bank_list_comp_yn TEXT DEFAULT 'Y', grantlist_complete_yn TEXT DEFAULT 'Y', vernacular_title TEXT, date_of_electronic_publication TIMESTAMP, country TEXT, medline_ta TEXT NOT NULL, nlm_unique_id TEXT, xml_file_name TEXT NOT NULL, number_of_references TEXT, citation_owner TEXT DEFAULT 'NLM', citation_status TEXT, PRIMARY KEY (pmid));
CREATE INDEX pk_med_citation on medline_citation(pmid, pub_date_year, left(journal_title, 255), country);

#==============================================================
# TABLE: medline_author
#==============================================================
CREATE TABLE medline_author (pmid INTEGER NOT NULL, last_name TEXT, fore_name TEXT, first_name TEXT, middle_name TEXT, initials TEXT, suffix TEXT, affiliation TEXT, collective_name TEXT);
CREATE INDEX idx_author on medline_author(pmid, left(affiliation, 255));

#==============================================================
# TABLE: medline_chemical_list
#==============================================================
CREATE TABLE medline_chemical_list (pmid INTEGER NOT NULL, registry_number TEXT, name_of_substance TEXT NOT NULL);
CREATE INDEX idx_m_chem on medline_chemical_list(pmid, left(name_of_substance, 255));

#==============================================================
# TABLE: medline_mesh_heading 
#==============================================================
CREATE TABLE medline_mesh_heading(pmid INTEGER NOT NULL, descriptor_name TEXT NOT NULL, descriptor_ui TEXT, descriptor_name_major_yn TEXT DEFAULT 'N', qualifier_name TEXT NOT NULL, qualifier_ui TEXT, qualifier_name_major_yn TEXT DEFAULT 'N');
CREATE INDEX pk_med_meshheading on medline_mesh_heading(pmid, descriptor_name, qualifier_name);

#==============================================================
# TABLE: medline_comments_corrections 
#==============================================================
CREATE TABLE medline_comments_corrections (pmid INTEGER NOT NULL, ref_pmid TEXT, type TEXT, ref_source TEXT);
CREATE INDEX idx_comments_pmid on medline_comments_corrections(pmid);

#==============================================================
# TABLE: medline_citation_subsets 
#==============================================================
CREATE TABLE medline_citation_subsets(pmid INTEGER NOT NULL, citation_subset TEXT NOT NULL);
CREATE INDEX pk_med_cit_sub on medline_citation_subsets(pmid, citation_subset);

#==============================================================
# TABLE: medline_article_publication_type 
#==============================================================
CREATE TABLE medline_article_publication_type( pmid INTEGER NOT NULL, publication_type TEXT);
CREATE INDEX idx_pub_type_pmid on medline_article_publication_type(pmid);

#==============================================================
# TABLE: medline_article_language 
#==============================================================
CREATE TABLE medline_article_language(pmid INTEGER NOT NULL, language TEXT);
CREATE INDEX idx_lang on medline_article_language(pmid, language);

#==============================================================
# TABLE: medline_grant 
#==============================================================
CREATE TABLE medline_grant(pmid INTEGER NOT NULL, grant_id TEXT NOT NULL, acronym TEXT, agency TEXT, country TEXT);
CREATE INDEX pk_medline_grant on medline_grant(pmid, grant_id, country);

#==============================================================
# TABLE: medline_data_bank 
#==============================================================
CREATE TABLE medline_data_bank(pmid INTEGER NOT NULL, accession_number TEXT NOT NULL);
CREATE INDEX idx_data_bank_pmid on medline_data_bank(pmid);

#==============================================================
# TABLE: medline_personal_name_subject 
#==============================================================
CREATE TABLE medline_personal_name_subject (pmid INTEGER NOT NULL, last_name TEXT, fore_name TEXT, first_name TEXT, middle_name TEXT, initials TEXT, suffix TEXT);
CREATE INDEX idx_pers_name_pmid on medline_personal_name_subject(pmid);

#==============================================================
# TABLE: medline_citation_other_id 
#==============================================================
CREATE TABLE medline_citation_other_id(pmid INTEGER NOT NULL, source TEXT, other_id TEXT);
CREATE INDEX idx_other_id_pmid on medline_citation_other_id(pmid);

#==============================================================
# TABLE: medline_investigator 
#==============================================================
CREATE TABLE medline_investigator (pmid	INTEGER NOT NULL, last_name TEXT, fore_name TEXT, first_name TEXT, middle_name TEXT, initials TEXT,  suffix TEXT, affiliation TEXT);
CREATE INDEX idx_invest_pmid on medline_investigator(pmid);
