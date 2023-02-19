PRAGMA encoding = 'UTF-8';
PRAGMA page_size = 8192;
-- do not verify contraints on loading
PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS doc;
CREATE TABLE doc (
    -- UniMARC BnF documents records
    -- doc https://www.bnf.fr/sites/default/files/2019-01/Unimarc%2B%28B%29_201901_conversion.pdf
    -- …-1969
    -- CGI/P1187* https://api.bnf.fr/notices-bibliographiques-des-catalogues-retroconvertis-imprimes-et-audiovisuel
    -- ftp://PRODUIT_RETRO:b9rZ2As7@pef.bnf.fr/PRODUIT_RETRO/CGI/CGI_2021/CGI_2021_Unimarc_UTF8/P1187*.UTF8
    -- 1970-2020
    -- BNF-Livres/P174* https://api.bnf.fr/notices-bibliographiques-de-la-bibliographie-nationale-francaise
    -- ftp://PRODUIT_RETRO:b9rZ2As7@pef.bnf.fr/PRODUIT_RETRO/BNF-Livres/BNF-Livres_2021/BNF-Livres_2021_Unimarc_UTF8/P174*.UTF8
    -- biblio ref
    id           INTEGER,  -- from 003
    title  TEXT NOT NULL,  -- uniform title 500$a, if (lang != 'fre') note 300$a, title proper 200$a
    desc            TEXT,  -- long title, concat 200
    year         INTEGER,  -- publication year, 100, 210$d
    -- resp
    byline          TEXT,  -- for a bibliographic ref
    authors      INTEGER,  -- count of author
    auth1        INTEGER,  -- id of first author
    type1        INTEGER,  -- type of first author (pers or corp)
    gender1      INTEGER,  -- gender of first author
    order1       INTEGER,  -- first, second… title for auth1
    -- editorial
    address         TEXT,  -- 210$r editorial address
    place           TEXT,  -- 210$a publication place 
    place_group     TEXT,  -- publication place, for grouping
    place_like      TEXT,  -- publication place, for search
    publisher       TEXT,  -- éditeur extrait de l’adresse éditoriale, 210$c
    publisher_group TEXT,  -- éditeur extrait de l’adresse éditoriale, 210$c
    publisher_like  TEXT,  -- éditeur extrait de l’adresse éditoriale, 210$c
    format       INTEGER,  -- in-° : 8, 4, 12… 930$5, 215$a
    pages        INTEGER,  -- page count, 215$a
    -- coding
    type            TEXT,  -- https://www.marc21.ca/M21/COD/RDA-CON-MARC.html, 181$c, 200$b
    lang            TEXT,  -- language, 101$a 
    translation     TEXT,  -- is translation ? 101'0, original lang
    clement         TEXT,  -- 930$5
    clement_letter  TEXT,  -- 930$5
    country         TEXT,  -- 102$a country code
    -- control 
    file   TEXT NOT NULL,  -- source File
    url    TEXT NOT NULL,  -- url catalog, 003
    gallica         TEXT,  -- url, 856$a
    PRIMARY KEY(id ASC)
);

CREATE INDEX doc_auth ON doc(auth1, year);
CREATE INDEX doc_clement ON doc(year, clement);
CREATE INDEX doc_clement2 ON doc(clement, year);
CREATE INDEX doc_format ON doc(year, format, pages);
CREATE INDEX doc_gender ON doc(year, gender1);
CREATE INDEX doc_lang ON doc(year, lang);
CREATE INDEX doc_order ON doc(year, order1);
CREATE INDEX doc_pages ON doc(year, pages);
CREATE INDEX doc_place ON doc(year, place_group);
CREATE INDEX doc_place2 ON doc(place_group, year);
CREATE INDEX doc_place3 ON doc(year, place_like);
CREATE INDEX doc_place4 ON doc(place_like, year);
CREATE INDEX doc_publisher ON doc(year, publisher_group);
CREATE INDEX doc_publisher2 ON doc(publisher_group, year);
CREATE INDEX doc_type ON doc(type1, year);
CREATE INDEX doc_type2 ON doc(year, type1, gender1);


CREATE TABLE contrib (
    doc         INTEGER NOT NULL,
    auth        INTEGER NOT NULL,
    field       INTEGER NOT NULL,
    role        INTEGER NOT NULL,
    -- redundancies
    type        INTEGER, -- code for contrib, infered from field & role 
    year        INTEGER, -- redundant with doc.year
    birthyear   INTEGER, -- redundant with auth, track dates error
    id          INTEGER, -- rowid auto
    PRIMARY KEY(id ASC)
);

CREATE INDEX contrib_role  ON contrib(role);
CREATE INDEX contrib_field ON contrib(field, role);
CREATE INDEX contrib_auth ON contrib(auth, year, type);
CREATE INDEX contrib_doc ON contrib(doc);

CREATE TABLE about (
    doc         INTEGER NOT NULL,
    auth        INTEGER NOT NULL,
    year        INTEGER, -- copied from doc, for plot perfs
    id          INTEGER, -- rowid auto
    PRIMARY KEY(id ASC)
);

CREATE INDEX about_doc  ON about(doc);
CREATE INDEX about_auth ON about(auth, year);


CREATE TABLE auth (
    -- UniMARC BnF autorités
    -- doc https://www.bnf.fr/sites/default/files/2019-01/UNIMARC%28A%29_2018_conversion.pdf
    -- https://api.bnf.fr/notices-dautorite-personnes-collectivites-oeuvres-lieux-noms-communs-de-bnf-catalogue-general
    -- ftp://PRODUIT_RETRO:b9rZ2As7@pef.bnf.fr/PRODUIT_RETRO/Pcts/Pcts_2021/Pcts_2021_Unimarc_UTF8/P1486_*.UTF8

    id             INTEGER, -- auth#003, doc#7**$3
    type  INTEGER NOT NULL, -- 1=pers, 2=corp
    name     TEXT NOT NULL, -- auth#200$a ; auth#210$a, auth#210$b 
    role              TEXT, -- auth200$c ; auth210$c
    note              BLOB, -- auth#300$a information about author

    deform   TEXT NOT NULL, -- lower case with no accents, for search

    -- 
    docs           INTEGER, -- doc count as first author
    doc1           INTEGER, -- date of first doc

    -- pers infos
    given             TEXT, -- auth#200$b
    gender         INTEGER, -- auth#120$b or inferred from given
    birthyear      INTEGER, -- birth year: auth#200$f, auth#103$a
    deathyear      INTEGER, -- death year: auth#200$f, auth#103$a
    birthplace        TEXT, -- birth place
    deathplace        TEXT, -- death place
    age            INTEGER, -- death - birth
    generation     INTEGER, -- a date, birtyear or doc1

    file              TEXT, -- source File from auth marc, or NULL from doc
    url               TEXT, -- url catalog, auth#003, or NULL
    PRIMARY KEY(id ASC)
);

CREATE INDEX auth_given ON auth(given);
CREATE INDEX auth_name ON auth(name);
CREATE INDEX auth_deform ON auth(deform, generation);
CREATE INDEX auth_docs ON auth(docs DESC, deform);
CREATE INDEX auth_doc1 ON auth(doc1, gender);

