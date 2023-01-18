PRAGMA encoding = 'UTF-8';
PRAGMA page_size = 8192;
-- do not verify contraints on loading
PRAGMA foreign_keys = OFF;

CREATE TABLE doc (
    -- UniMARC BnF documents records
    -- CGI/P1187* https://api.bnf.fr/notices-bibliographiques-des-catalogues-retroconvertis-imprimes-et-audiovisuel
    -- ftp://PRODUIT_RETRO:b9rZ2As7@pef.bnf.fr/PRODUIT_RETRO/CGI/CGI_2021/CGI_2021_Intermarc_UTF8/P1187*.UTF8
    --
    -- BNF-Livres/P174* https://api.bnf.fr/notices-bibliographiques-de-la-bibliographie-nationale-francaise
    -- ftp://PRODUIT_RETRO:b9rZ2As7@pef.bnf.fr/PRODUIT_RETRO/BNF-Livres/BNF-Livres_2021/BNF-Livres_2021_Unimarc_UTF8/P174*.UTF8
    file        TEXT NOT NULL, -- source File
    -- marc        BLOB,       -- full marc record (for debug)
    url         TEXT NOT NULL, -- url catalog, 003
    gallica     TEXT,          -- url, 856$a
    type        TEXT,          -- https://www.marc21.ca/M21/COD/RDA-CON-MARC.html, 181$c, 200$b
    lang        TEXT,          -- language, 101$a 
    title       TEXT NOT NULL, -- uniform title 500$a, if (lang != 'fre') note 300$a, title proper 200$a
    title_c     INTEGER,       -- char count of title
    translation TEXT,          -- is translation ? 101'0, original lang
    year        INTEGER,       -- publication year, 100, 210$d
    place       TEXT,          -- publication place, 210$a
    country     TEXT,          -- 102$a country code
    region      TEXT,          -- infer a region from 
    publisher   TEXT,          -- éditeur extrait de l’adresse éditoriale, 210$c
    clement_letter TEXT,       -- 930$5
    clement_no  TEXT,          -- 930$5
    format      INTEGER,       -- in-° : 8, 4, 12… 930$5, 215$a
    pages       INTEGER,       -- page count, 215$a
    debug       TEXT,          -- a temp message to check data
    id          INTEGER,       -- rowid auto
    PRIMARY KEY(id ASC)
);

CREATE INDEX doc_year ON doc(year, type);
CREATE INDEX doc_lang ON doc(year, lang);
CREATE INDEX doc_type ON doc(type, year);
CREATE INDEX doc_translation ON doc(year, translation);
CREATE INDEX doc_pages ON doc(year, pages);
CREATE INDEX doc_publisher ON doc(year, publisher);
CREATE INDEX doc_place ON doc(year, place);
CREATE INDEX doc_format ON doc(year, format, pages);
CREATE INDEX doc_debug ON doc(debug, year);

CREATE TABLE place (
    -- BnF geo names, InterMARC
    -- P2819* https://api.bnf.fr/notices-dautorite-personnes-collectivites-oeuvres-lieux-noms-communs-de-bnf-catalogue-general
    file        TEXT NOT NULL, -- source File
    form        TEXT,          -- form (authority or rejected)
    parent      INTEGER,       -- identifier of parent for rejected form
    region      TEXT,          -- 
    id          INTEGER,       -- rowid auto
    PRIMARY KEY(id ASC)
);

CREATE TABLE doc_pers (
    doc         INTEGER,
    pers        INTEGER,
    role        STRING,
    id          INTEGER,       -- rowid auto
    PRIMARY KEY(id ASC)
);

CREATE TABLE pers (
    -- UniMARC BnF autorités
    -- https://api.bnf.fr/notices-dautorite-personnes-collectivites-oeuvres-lieux-noms-communs-de-bnf-catalogue-general
    -- ftp://PRODUIT_RETRO:b9rZ2As7@pef.bnf.fr/PRODUIT_RETRO/Pcts/Pcts_2021/Pcts_2021_Unimarc_UTF8/P1486_*.UTF8
    file        TEXT NOT NULL, -- source File
    url         TEXT NOT NULL, -- url catalog, 003
    nb          TEXT NOT NULL, -- doc700$3
    surname     TEXT NOT NULL, -- auth200$a
    forename    TEXT NOT NULL, -- auth200$b
    id          INTEGER,       -- rowid auto
    PRIMARY KEY(id ASC)
);
