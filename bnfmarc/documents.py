"""
Part of bnfmarc https://github.com/bnfhack/bnfmarc
Copyright (c) 2022 frederic.glorieux@fictif.org
MIT License https://opensource.org/licenses/mit-license.php
Code policy PEP8 https://www.python.org/dev/peps/pep-0008/
"""

import argparse
import glob
import logging
import pymarc
import os
import re
import sqlite3
import sys


# shared sqlite3 objects
con = None

def connect(cataviz_db):
    "Connect database and create tables"
    global con
    if os.path.isfile(cataviz_db):
        os.remove(cataviz_db)
    con = sqlite3.connect(cataviz_db)
    cur = con.cursor()
    sql_file = os.path.join(os.path.dirname(__file__), 'cataviz.sql')
    with open(sql_file, "r", encoding='utf-8') as h:
        sql = h.read()
    cur.executescript(sql)



def walk(marc_dir):
    """Parse marc files"""
    if not os.path.isdir(marc_dir):
        raise Exception("Dir not found for marc data:\"" + marc_dir + "\"")
    for root, dirs, files in os.walk(marc_dir):
        for name in files:
            marc_file = os.path.join(root, name)
            if (name.startswith('P1187')):
                docs(marc_file)
                continue
    con.commit()

def clement(r):
    """Get format and other info from clement cotation

RES FOL-T29-4

    """
    for f in r.get_fields('930'):
        found = re.search(r"(FR-\d{9}):(.*)", f['5'])
        if (found == None):
            # never arrive, all docs from FR(ench) BnF
            return None


def type(r, doc_values):
    """Get rdacontent type"""
    doc_values['type'] == None
    if (r['181'] != None):
        for f in r.get_fields('181'):
            if (f['2'] != 'rdacontent'):
                continue
            doc_values['type'] = f['c']
            if (doc_values['type'] != None):
                return
    # never arrive, kept for memory
    # 200, fully covering
    type = r['200']['b']
    if (type == 'Texte imprimé'):
        doc_values['type'] == 'txt'
    elif (type == 'Image fixe'):
        doc_values['type'] == 'sti'
    elif (type == 'Musique imprimée'):
        doc_values['type'] == 'ntm'

def lang(r, doc_values):
    # print(f.indicator2)
    pass


def title(r, doc_values):
    if (r['500'] != None and r['500']['a'] != None):
        doc_values['title'] = r['500']['a']
    # translated title ?
    if (r['200'] != None and r['200']['a'] != None):
        doc_values['title'] = r['200']['a']

def year(r, doc_values):
    doc_values['year'] = None
    doc_values['year_cert'] = None
    str = r['100'].value()[9:13]
    year = str_year(str)
    if (year != None):
        doc_values['year_cert'] = 1
        doc_values['year'] = year
        return
    while True:
        if (r['210'] == None):
            break
        if (r['210']['d'] == None):
            break
        # find [1810]
        found = re.search(r'(\-?[\d\?\.]+)', r['210']['d'])
        if (found == None):
            break
        str = found.group(1)
        year = str_year(str)
        if (year == None):
            break
        doc_values['year_cert'] = 1
        doc_values['year'] = year
        return
    # get date from author?
    """
    while True:
        if (r['700'] == None):
            break
        if (r['700']['f'] == None):
            break
        found = re.search(r'\-([\d\?\.]+)', r['700']['f'])
    """
    return

def str_year(str):
    if (str == None):
        return None
    try:
        year = int(str)
        return year
    except ValueError:
        return None


def docs(marc_file):
    global con
    print(marc_file)
    doc_values = {
        'file': os.path.basename(marc_file),
        'url': '',
        'type': None,
        'lang': None,
        'title': '',
        'translation': None,
        'year': None,
        'year_cert': None,
        'place': None,
        'publisher': None,
        'clement_letter': None,
        'clement_no': None,
        'format': None,
        'pages': None,
    }
    doc_sql = "INSERT INTO doc (" + ", ".join([*doc_values]) + ") VALUES (:" + ", :".join([*doc_values]) +")"
    cur = con.cursor()
    with open(marc_file, 'rb') as handle:
        reader = pymarc.MARCReader(
            handle, 
            to_unicode=True,
            force_utf8=True
        )
        for r in reader:
            echo = False
            year(r, doc_values)
            type(r, doc_values)
            title(r, doc_values)
            cur.execute(doc_sql, doc_values)


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Crawl a folder of marc file to test pymarc',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('cataviz_db', nargs=1,
    help='Sqlite database to generate')

    args = parser.parse_args()
    connect(args.cataviz_db[0])
    marc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/')
    walk(marc_dir)

if __name__ == '__main__':
    sys.exit(main())
