"""
Part of bnfmarc https://github.com/bnfhack/bnfmarc
Copyright (c) 2022 frederic.glorieux@fictif.org
MIT License https://opensource.org/licenses/mit-license.php
Code policy PEP8 https://www.python.org/dev/peps/pep-0008/
"""


""" Update fields for more efficient queries
"""
import argparse
import sqlite3
import sys

# local
import bnfmarc

# shared sqlite3 connexion
con = None


def doc_order():
    """Loop on all docs to 
    """
    global con
    # a cursor for updates
    cur_up = con.cursor()
    sql_up = "UPDATE doc SET order1 = ? WHERE id = ?"
    cur_sel = con.cursor()
    auth_last = -1
    order = 0
    # null date at the end
    sql = "SELECT id, auth1, year FROM doc WHERE auth1 IS NOT NULL ORDER BY auth1, year NULLS LAST;"
    nrows = cur_sel.execute(sql)
    while True:
        row = cur_sel.fetchone()
        if row == None:
            break
        doc_id = row[0]
        if auth_last != row[1]:
            order = 1
            auth_last = row[1]
        else:
            order = order + 1
        cur_up.execute(sql_up, [order, doc_id])
    


def main() -> int:
    global con
    parser = argparse.ArgumentParser(
        description='Loop on rows to correct and update',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('cataviz_db', nargs=1,
    help='Sqlite database to generate')
    args = parser.parse_args()
    con = bnfmarc.connect(args.cataviz_db[0])
    doc_order()
    con.commit()

if __name__ == '__main__':
    sys.exit(main())