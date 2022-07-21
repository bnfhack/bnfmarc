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
            if (name.startswith('P174_') or name.startswith('P1187_')): 
                # P1187_, <= 1970, P174_ > 1970 
                docs(marc_file)
                continue
    con.commit()

def desc(r, doc_values):
    """Get physical informations. Let clement() work after for more precise info on folio """
    if (r['215'] == None):
        return
    format = None
    while (r['215']['a'] != None): # pages
        folio = r['215']['a']
        found = re.search(r"(\d+)[ ]*p\.", r['215']['a'], re.IGNORECASE)
        if (found != None):
            pages = int(found.group(1))
            if (pages > 9999):
                 pages = 1000 # error 
            doc_values['pages'] = pages
            break
        found = re.search(r"pièce|placard", r['215']['a'], re.IGNORECASE)
        if (found != None):
            doc_values['pages'] = 1
            break
        # doc_values['debug'] = str(r['215'])
        break
    if (r['215']['d'] != None):
        format = r['215']['d']
    if (format == None):
        return

    found = re.search(r"In[ \-]*(\d+)", format, re.IGNORECASE)
    if (found != None):
        doc_values['format'] = found.group(1)
        return
    found = re.search(r"in-fol", format, re.IGNORECASE)
    if (found != None):
        doc_values['format'] = 2
        return
    found = re.search(r"gr[\. ]+fol[\. ]?", format, re.IGNORECASE)
    if (found != None):
        doc_values['format'] = 1
        # placard, affiche ? ou presse ?
        return
    found = re.search(r"(\d+) *cm", format, re.IGNORECASE)
    if (found != None):
        cm = int(found.group(1))
        if (cm < 10):
            doc_values['format'] = 32
        if (cm < 16):
            doc_values['format'] = 16
        if (cm < 20):
            doc_values['format'] = 12
        if (cm < 25):
            doc_values['format'] = 8
        if (cm < 30):
            doc_values['format'] = 4
        else:
            doc_values['format'] = 2
        return


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
    doc_values['lang'] = 'fre'
    if (r['101'] == None or r['101']['a'] == None):
        # http://catalogue.bnf.fr/ark:/12148/cb43650693f
        return
    doc_values['lang'] = r['101']['a']
    doc_values['translation'] = r['101'].indicator1
    if (r['101']['c'] == None):
        if (r['101'].indicator1 == 1):
            print(r)
        return
    doc_values['translation'] = r['101']['c']


def title(r, doc_values):
    if (r['500'] != None and r['500']['a'] != None):
        doc_values['title'] = r['500']['a']
        return
    # translated title ?
    if (r['200'] != None and r['200']['a'] != None):
        doc_values['title'] = r['200']['a']
        return
    if (r['200'] != None and r['200']['i'] != None):
        doc_values['title'] = r['200']['i']
        return
    doc_values['title'] = "[Sans titre]"

def url(r, doc_values):
    if (r['003'] == None):
        print(r)
    else:
        doc_values['url'] = r['003'].value()
    if (r['856'] != None and r['856']['u']):
        doc_values['gallica'] = r['856']['u']

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
    file = os.path.basename(marc_file)
    doc_values = {
        'file': None,
        # 'marc': None,
        'url': '',
        'gallica': None,
        'type': None,
        'lang': None,
        'title': '',
        'translation': None,
        'year': None,
        'place': None,
        'publisher': None,
        'clement_letter': None,
        'clement_no': None,
        'format': None,
        'pages': None,
        'debug': None,
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
            for key in doc_values:
                doc_values[key] = None
            doc_values['file'] = file
            doc_values['url'] = ''
            # doc_values['marc'] = str(r)
            year(r, doc_values)
            type(r, doc_values)
            url(r, doc_values)
            desc(r, doc_values) # before clement
            title(r, doc_values)
            lang(r, doc_values)
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
