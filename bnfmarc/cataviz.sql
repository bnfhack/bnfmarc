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
    byline          TEXT,  -- for a bibliographic ref
    year         INTEGER,  -- publication year, 100, 210$d
    title  TEXT NOT NULL,  -- uniform title 500$a, if (lang != 'fre') note 300$a, title proper 200$a
    desc            TEXT,  -- long title, concat 200
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
    id           INTEGER,  -- rowid auto
    PRIMARY KEY(id ASC)
);

CREATE INDEX doc_year ON doc(year, type);
CREATE INDEX doc_lang ON doc(year, lang);
CREATE INDEX doc_type ON doc(type, year);
CREATE INDEX doc_pages ON doc(year, pages);
CREATE INDEX doc_publisher ON doc(year, publisher_group);
CREATE INDEX doc_publisher2 ON doc(publisher_group, year);
CREATE INDEX doc_place ON doc(year, place_group);
CREATE INDEX doc_place2 ON doc(place_group, year);
CREATE INDEX doc_place3 ON doc(year, place_like);
CREATE INDEX doc_place4 ON doc(place_like, year);
CREATE INDEX doc_format ON doc(year, format, pages);
CREATE INDEX doc_translation ON doc(year, translation);
CREATE INDEX doc_clement ON doc(year, clement_letter, clement_no);


CREATE TABLE contrib (
    doc         INTEGER NOT NULL,
    pers        INTEGER NOT NULL,
    field       INTEGER NOT NULL,
    role        INTEGER NOT NULL,

    year        INTEGER, -- redundant with doc
    birthyear   INTEGER, -- redundant with pers, track dates error
    type        INTEGER, -- code for kind of contrib
    id          INTEGER, -- rowid auto
    PRIMARY KEY(id ASC)
);

CREATE INDEX contrib_role  ON contrib(role);
CREATE INDEX contrib_field ON contrib(field, role);
CREATE INDEX contrib_pers ON contrib(pers, year, type);


CREATE TABLE pers (
    -- UniMARC BnF autorités
    -- doc https://www.bnf.fr/sites/default/files/2019-01/UNIMARC%28A%29_2018_conversion.pdf
    -- https://api.bnf.fr/notices-dautorite-personnes-collectivites-oeuvres-lieux-noms-communs-de-bnf-catalogue-general
    -- ftp://PRODUIT_RETRO:b9rZ2As7@pef.bnf.fr/PRODUIT_RETRO/Pcts/Pcts_2021/Pcts_2021_Unimarc_UTF8/P1486_*.UTF8
    name        TEXT NOT NULL, -- auth200$a
    given       TEXT,          -- auth200$b
    gender      INTEGER,       -- auth120$b inferred from given
    role        TEXT,          -- auth200$c
    deform      TEXT NOT NULL, -- lower case with no accents, for search


    birthyear   INTEGER,       -- birth year: auth200$f, auth103$a
    deathyear   INTEGER,       -- death year: auth200$f, auth103$a
    birthplace  TEXT,          -- birth place
    deathplace  TEXT,          -- death place
    note        BLOB,          -- information about author
    file        TEXT,          -- source File from auth marc, or NULL from doc
    url         TEXT,          -- url catalog, auth#003, or NULL
    nb          INT NOT NULL UNIQUE, -- doc700$3, auth#003

    age         INTEGER,       -- age at death (for demography)
    agedec      INTEGER,       -- âge à la mort, décade
    docs        INTEGER,       -- doc count as first author
    anthum      INTEGER,       -- doc count before death
    posthum     INTEGER,       -- doc count after death
    lang        TEXT,          -- main language for docs
    doc1        INTEGER,       -- date of first doc
    age1        INTEGER,       -- age at first doc

    id          INTEGER,       -- rowid auto
    PRIMARY KEY(id ASC)
);

CREATE INDEX pers_given ON pers(given);
CREATE INDEX pers_name ON pers(name);
CREATE INDEX pers_deform ON pers(deform);
CREATE INDEX pers_docs ON pers(docs DESC, deform);
CREATE INDEX pers_doc1 ON pers(doc1, gender);

