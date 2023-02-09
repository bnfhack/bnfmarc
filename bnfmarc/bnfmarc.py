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
    # casefold(), lowercase
    # normalize NFD, decompose letters and diacritics
    # strip diacritics and other non letters
    # normalize space (split on ' ' and join on ' ')
    chars = []
    show = False
    for c in unicodedata.normalize('NFD', s.casefold()):
        cat = unicodedata.category(c)
        if c == 'œ':
            chars.append('o')
            chars.append('e')
            continue
        if c == 'æ':
            chars.append('a')
            chars.append('e')
            continue
        if cat == 'Ll':
            chars.append(c)
            continue
        cat0 = cat[0]
        if c == '$': # bad marc segmentation
            break
        if cat == 'Mn': # diacritic
            continue
        if cat == 'Lm' or cat == 'Sk': # Letter modifier, ex: Muʻtamad
            continue
        if cat == 'Cc' or cat == 'Cf': # Other, Control, le bibliophile jean
            chars.append(' ')
            continue            
        if cat0 == 'M' or cat0 == 'P' or cat0 == 'Z':
            chars.append(' ')
            continue
        if cat == 'Nd':
            chars.append(c)
            continue
        chars.append(c)
    deform = " ".join(''.join(chars).split())
    return deform
