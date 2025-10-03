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
    """Loop on all docs to define their order for first author
    """
    global con
    # a cursor for updates
    update_cur = con.cursor()
    order1_sql = "UPDATE doc SET order1 = ? WHERE id = ?"
    hume1_sql = "UPDATE doc SET hume1 = ? WHERE id = ?"
    auth_cur = con.cursor()
    auth_sql = "SELECT deathyear, birthyear, name, given FROM auth WHERE id = ?"
    doc_cur = con.cursor()
    auth_last = -1
    auth_death = None;
    doc_order1 = -1
    doc_hume1 = -1
    # null date at the end
    doc_sql = "SELECT id, auth1, year, title, byline FROM doc WHERE auth1 IS NOT NULL ORDER BY auth1, year NULLS LAST;"
    nrows = doc_cur.execute(doc_sql)
    while True:
        doc_row = doc_cur.fetchone()
        if doc_row == None:
            break
        doc_id = doc_row[0]
        doc_year = doc_row[2]
        doc_auth1 = doc_row[1]
        if auth_last != doc_auth1:
            doc_order1 = 1
            doc_hume1 = 1
            auth_last = doc_auth1
            res = auth_cur.execute(auth_sql, (auth_last,))
            auth_row = res.fetchone()
            if auth_row is None:
                auth_death = None
                print(str(doc_row[3]) + ', ' + str(doc_row[4]) + ' ' + str(doc_year) + " " + str(doc_auth1))
            elif auth_row[0] is not None:
                auth_death = auth_row[0]
            elif auth_row[1] is not None:
                auth_death = auth_row[1] + 70
            elif doc_year is not None:
                auth_death = doc_year + 50
            else:
                auth_death = None
            # print(str(name) + ' ' + str(given) +  ' (' + str(birth) + ', ' + str(death) + ') ' + str(row[2]))
        else:
            doc_order1 = doc_order1 + 1
            if doc_year is None:
                doc_hume1 = 2
            elif auth_death is None:
                doc_hume1 = 2
            elif doc_year > auth_death:
                doc_hume1 = 3
            else:
                doc_hume1 = 2
        # update_cur.execute(sql_up, [order, doc_id])
        update_cur.execute(hume1_sql, [doc_hume1, doc_id])
    
def update():
    global con
    cur = con.cursor()
    sql_file = os.path.join(os.path.dirname(__file__), 'update.sql')
    with open(sql_file, 'r') as file:
        sql = file.read()
    cur.executescript(sql)

def main() -> int:
    global con
    parser = argparse.ArgumentParser(
        description='apply update scripts after auths and docs insert',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('cataviz_db', nargs=1,
    help='Sqlite database to generate')
    args = parser.parse_args()
    db_file = args.cataviz_db[0]
    con = bnfmarc.connect(db_file)
    doc_order()
    # update() # not tested
    con.commit()
    

if __name__ == '__main__':
    sys.exit(main())