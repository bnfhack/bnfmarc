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
import shutil
import sqlite3
import sys
# local
import bnfmarc

# shared sqlite3 connexion
con = None
cur_pers = None
cur_writes = None
pers_nb = {}
writes_cols = ['doc', 'pers', 'role']
writes_sql = "INSERT INTO doc_pers (" + ", ".join(writes_cols) + ") VALUES (:" + ", :".join(writes_cols) +")"


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

def pers(r, doc_id):
    """Write link between doc to pers author"""
    global pers_nb, cur_pers, writes_sql, cur_writes
    for f in r.get_fields('700'):
        if (f['3'] is None):
            # ~10 cases found
            continue
        nb = int(f['3'])
        if (nb in pers_nb):
            pers_id = pers_nb[nb]
        else:
            sql = 'SELECT id FROM pers WHERE nb = ?'
            rows = cur_pers.execute(sql, (nb,)).fetchall()
            count = len(rows)
            if count > 1: # impossible index UNIQUE, but who knows ?
                continue
            # no authority record for this author
            if count == 0:
                # a few cases, a line with pers id but with no name
                continue
            pers_id = int(rows[0][0])
            pers_nb[nb] = pers_id
        if f['4'] is not None:
            role = int(f['4'])
        else:
            role = 70
        cur_writes.execute(
            writes_sql, 
            {'doc': doc_id, 'pers': pers_id, 'role': role}
        )


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
            # ????
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
        print("NO URL ?")
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
            doc_values['url'] = str(r['003'].value().strip())
            # doc_values['marc'] = str(r)
            year(r, doc_values)
            type(r, doc_values)
            url(r, doc_values)
            desc(r, doc_values) # before clement
            title(r, doc_values)
            lang(r, doc_values)
            place(r, doc_values)
            publisher(r, doc_values)
            # write doc record
            cur.execute(doc_sql, doc_values)
            doc_id = cur.lastrowid
            # link to author
            pers(r, doc_id)



def main() -> int:
    global con, cur_pers, cur_writes
    parser = argparse.ArgumentParser(
        description='Crawl a folder of marc file to generate an sqlite base',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('cataviz_db', nargs=1,
    help='Sqlite database to generate')

    args = parser.parse_args()
    # tmp, copy file to keep pers

    db_file = args.cataviz_db[0] + '2'
    shutil.copyfile(args.cataviz_db[0], db_file)
    con = bnfmarc.connect(db_file)
    cur_pers = con.cursor()
    cur_writes = con.cursor()
    marc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/')

    # if (name.startswith('P174_') or name.startswith('P1187_')): 
    for marc_file in glob.glob(os.path.join(marc_dir, "P1187_*.UTF8")):
        docs(marc_file)
    for marc_file in glob.glob(os.path.join(marc_dir, "P174_*.UTF8")):
        docs(marc_file)
    con.commit()

if __name__ == '__main__':
    sys.exit(main())
