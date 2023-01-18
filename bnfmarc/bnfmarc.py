"""
Part of bnfmarc https://github.com/bnfhack/bnfmarc
Copyright (c) 2022 frederic.glorieux@fictif.org
MIT License https://opensource.org/licenses/mit-license.php
Code policy PEP8 https://www.python.org/dev/peps/pep-0008/
"""

import os
import sqlite3


def connect(cataviz_db):
    "Connect database and create tables"
    if os.path.isfile(cataviz_db):
        os.remove(cataviz_db)
    con = sqlite3.connect(cataviz_db)
    cur = con.cursor()
    sql_file = os.path.join(os.path.dirname(__file__), 'cataviz.sql')
    with open(sql_file, "r", encoding='utf-8') as h:
        sql = h.read()
    cur.executescript(sql)
    return con

