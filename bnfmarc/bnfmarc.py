"""
Part of bnfmarc https://github.com/bnfhack/bnfmarc
Copyright (c) 2022 frederic.glorieux@fictif.org
MIT License https://opensource.org/licenses/mit-license.php
Code policy PEP8 https://www.python.org/dev/peps/pep-0008/
"""

import os
import sqlite3
import unicodedata

def connect(cataviz_db, create=False):
    "Connect database and create tables"
    if os.path.isfile(cataviz_db):
        if not create:
            return sqlite3.connect(cataviz_db)
        # if create, delete old
        os.remove(cataviz_db)
    con = sqlite3.connect(cataviz_db)
    cur = con.cursor()
    sql_file = os.path.join(os.path.dirname(__file__), 'cataviz.sql')
    with open(sql_file, "r", encoding='utf-8') as h:
        sql = h.read()
    cur.executescript(sql)
    return con

# returns a normalized form lowercase with no diacritics
def deform(s):
    # 1. casefold(), lowercase
    # 2. normalize NFD, decompose letters and diacritics
    # 3. ''.join(), split by char
    # 4. category() != 'Mn', Mn="Mark, nonspacing", strip diacritics 
    return ''.join(c for c 
        in unicodedata.normalize('NFD', s.casefold())
        if unicodedata.category(c) != 'Mn'
    )
