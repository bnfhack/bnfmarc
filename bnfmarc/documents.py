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
    desc = None
    if (r['215'] != None):
        desc = str(r['215'])
    else:
        desc = str(r['210'])

    found = re.search(r"(\d+)[ ]*p\.", desc, re.IGNORECASE)
    if (found != None):
        pages = int(found.group(1))
        if (pages > 9999):
            pages = 1000 # error 
        doc_values['pages'] = pages
    if (doc_values['pages'] == None):
        found = re.search(r"pièce|placard", desc, re.IGNORECASE)
        if (found != None):
            doc_values['pages'] = 1
    # format
    # space error: 12 juin 1782, in-fol.
    found = re.search(r"In[ \-]*(\d+)", desc, re.IGNORECASE)
    if (found != None):
        doc_values['format'] = found.group(1)
        return
    found = re.search(r"in-fol", desc, re.IGNORECASE)
    if (found != None):
        doc_values['format'] = 2
        return
    found = re.search(r"gr[\. ]+fol[\. ]?", desc, re.IGNORECASE)
    if (found != None):
        doc_values['format'] = 1
        # placard, affiche ? ou presse ?
        return
    # 8°
    found = re.search(r"(\d+)°", desc, re.IGNORECASE)
    if (found != None):
        doc_values['format'] = found.group(1)
        return
    found = re.search(r"(\d+) *cm", desc, re.IGNORECASE)
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

def publisher(r, doc_values):
    f = None
    if (r['214'] != None):
        f = r['214']
    elif (r['210'] != None):
        f = r['210']
    else:
        return
    if (f['c'] != None):
        doc_values['publisher'] = f['c']
        return
    elif (f['r'] == None):
        # What in this field ?
        return


def place(r, doc_values):
    if (r['620'] != None and r['620']['d'] != None):
        doc_values['place'] = r['620']['d']
        return
    f = None
    if (r['214'] != None):
        f = r['214']
    elif (r['210'] != None):
        f = r['210']
    else:
        return
    if (f['a'] != None):
        doc_values['place'] = f['a']
        return
    elif (f['r'] == None):
        # What in this field ?
        return
    # An editorial place could be parsed here, but most of work have been done by BnF
    return
    val = f['r']
    val = re.sub(r'[^\[\]\(\)]+|^[AÀ] ', 'a', val)

def country(r, doc_values):
    if (r['102'] != None and r['102']['a'] != None):
        doc_values['country'] = r['102']['a']
    # most of old records have no national bib country
    # post work may be done 


def year(r, doc_values):
    str = r['100'].value()[9:13]
    year = str_year(str)
    if (year != None and year > 1400 and year < 2030):
        doc_values['year'] = year
        return
    f = None
    if (r['214'] != None):
        f = r['214']
    elif (r['210'] != None):
        f = r['210']
    else: # no other field for date
        return
    val = None
    if (f['d'] != None):
        val = f['d']
    elif (f['r'] != None):
        val = f['r']
    else:
        return
    # find [1810]
    found = re.search(r'([\d\?\.]{4})', val)
    if (found == None):
        return
    str = found.group(1)
    year = str_year(str)
    if (year == None):
        return
    doc_values['year'] = year
    # do not serche date from author (reeditions)

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
        'country': None,
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
            place(r, doc_values)
            publisher(r, doc_values)
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
