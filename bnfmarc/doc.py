#!/usr/bin/python
# -*- coding: utf-8 -*-
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

""" Parse document records
https://www.bnf.fr/sites/default/files/2019-01/Unimarc%2B%28B%29_201901_conversion.pdf
"""

# shared sqlite3 connexion
con = None
# isolate a cursor for auth select, supposed to ease sqlite cache, not verified
auth_cur = None
# things for contrib table population
contrib_cur = None
contrib_cols = ['doc', 'auth', 'field', 'role']
contrib_sql = "INSERT INTO contrib (" + ", ".join(contrib_cols) + ") VALUES (:" + ", :".join(contrib_cols) +")"
# things for about (auth) table population
about_cur = None
about_cols = ['doc', 'auth']
about_sql = "INSERT INTO about (" + ", ".join(about_cols) + ") VALUES (:" + ", :".join(about_cols) +")"


year_min = 1400
year_max = 2020


def phys(r, doc_values):
    """Get physical informations. """
    phys = None
    if (r['215'] != None):
        phys = str(r['215'])
    else:
        phys = str(r['210'])

    found = re.search(r"(\d+)[ ]*p\.", phys, re.IGNORECASE)
    if (found != None):
        pages = int(found.group(1))
        if (pages > 9999):
            pages = 1000 # error 
        doc_values['pages'] = pages
    if (doc_values['pages'] == None):
        found = re.search(r"pièce|placard", phys, re.IGNORECASE)
        if (found != None):
            doc_values['pages'] = 1
    # format
    # space error: 12 juin 1782, in-fol.
    found = re.search(r"In[ \-]*(\d+)", phys, re.IGNORECASE)
    if (found != None):
        doc_values['format'] = found.group(1)
        return
    found = re.search(r"in-fol", phys, re.IGNORECASE)
    if (found != None):
        doc_values['format'] = 2
        return
    found = re.search(r"gr[\. ]+fol[\. ]?", phys, re.IGNORECASE)
    if (found != None):
        doc_values['format'] = 1
        # placard, affiche ? ou presse ?
        return
    # 8°
    found = re.search(r"(\d+)°", phys, re.IGNORECASE)
    if (found != None):
        doc_values['format'] = int(found.group(1))
        return
    found = re.search(r"(\d+) *cm", phys, re.IGNORECASE)
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


def clement(r, doc_values):
    """Get format and other info from clement cotation

RES FOL-T29-4
=930  \\$5FR-751131010:EL 8-Z-1935 (7)
=930  \\$5FR-751131010:8-CNLJD-13315
=930  \\$5FR-751131010:8-CNLJD-14804

    """
    fields = r.get_fields('930')
    if fields is None or len(fields) == 0:
        # no clement to find, > 1980 ?
        return
    i = 0
    for f in fields:
        i = i + 1
        cote =  None
        if (f['a'] is not None):
            cote = f['a']
            print(cote)
        elif (f['5'] is not None):
            cote = re.sub(r"(FR-\d{9}):([A-Z]+ )?", '', f['5'])
        if cote is None:
            continue
        found = re.search(r"((?P<format>[^\-]+)-)?(?P<clement>[A-Z][^ \-]*)(\-\d+| PIECE)", cote)
        if found is not None:
            if found.group('clement') is None:
                print("No clement ? " + cote + "|" + str(f))
                continue
            clement_format(found.group('format'), doc_values)
            doc_values['clement'] = found.group('clement')
            break # stop at first clement found
        # THETA ?
        found = re.search(r"((?P<format>[^\-]+)-)(?P<clement>THETA|TH)", cote)
        if found is not None:
            clement_format(found.group('format'), doc_values)
            doc_values['clement'] = found.group('clement')
            break # stop at first clement found


    for f in r.get_fields('930'):
        found = re.search(r"(FR-\d{9}):(.*)", f['5'])
        if (found == None):
            # never arrive, all docs from FR(ench) BnF
            return None

def clement_format(format, doc_values):
    if format is None or format == '':
        return
    if format == 'FOL':
        format = '2'
    if not format.isdigit():
        return
    doc_values['format'] = int(format)

def byline(r, doc_values):
    """Build a normalized byline from authors """
    authors = []
    # strip field without a name
    for field in r.get_fields('700'):
        if field['a'] is None:
            continue
        authors.append(field)
    for field in r.get_fields('710'):
        if field['a'] is None:
            continue
        authors.append(field)
    count = len(authors)
    if count == 0:
        return
    elif count == 1:
        doc_values['byline'] = authors[0]['a']
    elif count == 2:
        doc_values['byline'] = authors[0]['a'] + " & " + authors[1]['a']
    else:
        doc_values['byline'] = authors[0]['a'] + ", " + authors[1]['a'] + "… (" + count + ")"


def auth_links(r, doc_id):
    """Write links between doc to auth"""
    for field in r.get_fields('700'):
        contrib(doc_id, field)
    for field in r.get_fields('701'):
        contrib(doc_id, field)
    for field in r.get_fields('702'):
        contrib(doc_id, field)
    for field in r.get_fields('600'):
        about(doc_id, field)
    # corporate
    for field in r.get_fields('710'):
        contrib(doc_id, field)
    for field in r.get_fields('711'):
        contrib(doc_id, field)
    for field in r.get_fields('712'):
        contrib(doc_id, field)
    for field in r.get_fields('601'):
        about(doc_id, field)

""" Old when nb <> id
def auth_id(field):
    global auth_cache, auth_cur
    if (field['3'] is None):
        # ~10 cases found
        return None
    nb = int(field['3'][0:8])
    if (nb in auth_cache):
        return auth_cache[nb]

    sql = 'SELECT id FROM auth WHERE nb = ?'
    rows = auth_cur.execute(sql, (nb,)).fetchall()
    count = len(rows)
    if count > 1: # impossible, index UNIQUE, but who knows ?
        return
    # no authority record for this author
    if count == 0:
        # a few cases, a line with auth id but with no name
        return
    auth_id = int(rows[0][0])
    auth_cache[nb] = auth_id
    return auth_id
"""

def auth_id(field):
    if (field['3'] is None):
        # ~10 cases found
        return None
    id = int(field['3'][0:8])
    return id

def contrib(doc_id, field):
    global contrib_sql, contrib_cur
    id = auth_id(field)
    if id is None:
        return
    # sometimes no explicit function, set to author
    if field['4'] is None:
        role = 70
    else:
        role = int(field['4'])
    contrib_cur.execute(
        contrib_sql, 
        {'doc': doc_id, 'auth': id, 'field': int(field.tag), 'role': role}
    )

def about(doc_id, field):
    global about_sql, about_cur
    id = auth_id(field)
    if id is None:
        return
    about_cur.execute(
        about_sql, 
        {'doc': doc_id, 'auth': id}
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
    """Build title """
    title = None
    desc = []
    if (r['500'] is not None and r['500']['a'] is not None):
        title = r['500']['a']
        if (r['200'] is not None and r['200']['a'] is not None):
            desc.append(str(r['200']['a']))
    elif (r['200'] is None):
        doc_values['title'] = "[Sans titre]"
        return
    elif (r['200']['a'] is not None):
        title = r['200']['a']
    else: # No title ?
        doc_values['title'] = "[Sans titre]"
        return
    # reject article "Le diable boiteux"
    title = re.sub(r'(.+?) ? *(.*)', r'\2 (\1)', title)
    # ? Apologie des ceremonies de l'Eglise
    doc_values['title'] = title
    
    # long title
    if (r['200']['e'] is not None):
        desc.append(str(r['200']['e']))
    if (r['200']['h'] is not None):
        desc.append(str(r['200']['h']))
    if (r['200']['i'] is not None):
        desc.append(str(r['200']['i']))
    if len(desc) > 0:
        desc = ", ".join(desc)
        desc = re.sub(r'[@]', '', desc).strip()
        doc_values['desc'] = desc

def url(r, doc_values):
    if (r['003'] == None):
        print("NO URL ?")
        print(r)
        return
    doc_values['url'] = r['003'].value()
    #  http://catalogue.bnf.fr/ark:/12148/cb15037139g
    id = str(r['003']).split('ark:/12148/cb')[1]
    id = id[0:8] # id verified, is unique
    doc_values['id'] = int(id)
    
    if (r['856'] != None and r['856']['u']):
        doc_values['gallica'] = r['856']['u']

def address(r, doc_values):
    """Parse address line"""
    if r['210'] is None or r['210']['r'] is None:
        return
    doc_values['address'] = r['210']['r']
    # Halae Magdeburgicae : typis Orphanotrophei, 1715
    # [Paris, Louis Sevestre, 1715]
    address = r['210']['r'].strip(' ()[].,:;')
    members = re.split(r" *[,:;] *", address)
    if len(members) == 1:
        doc_values['publisher'] = members[0].strip()
    else :
        doc_values['place'] = members[0].strip()
        doc_values['publisher'] = members[1].strip()
        if len(members) > 2:
            found = re.search(r"(\d\d\d\d)", members[2], re.IGNORECASE)
            if found is not None:
                doc_values['year'] = str_year(found.group(1))


def publisher(r, doc_values):
    # if found in address
    publisher = doc_values['publisher']
    if r['210'] is not None and r['210']['c'] is not None:
        publisher = r['210']['c'].strip()
    # nothing found
    if not publisher:
        return
    # record orginal
    doc_values['publisher'] = publisher
    # [s.n.], [s.n.?]
    if re.search(r"s\. ?n[\.,]", publisher, flags=re.IGNORECASE) is not None:
        return
    # normalize value
    publisher = publisher.strip(' ()[].,:;')
    doc_values['publisher_group'] = publisher
    doc_values['publisher_like'] = bnfmarc.deform(doc_values['publisher'])


# find a place (after publisher and address line parsing)
def place(r, doc_values):
    place = None
    if (r['620'] is not None and r['620']['d'] is not None):
        place = r['620']['d']
    elif (r['214'] is not None and r['214']['a'] is not None):
        place = r['214']['a']
    elif (r['210'] is not None and r['210']['a'] is not None):
        place = r['210']['a']
    elif doc_values['place'] is not None:
        # found with address or publisher parsing
        place = doc_values['place']
    else:
        return
    # keep original
    doc_values['place'] = place
    # S. l.
    if re.search(r"s\. ?l[\.,]", place, flags=re.IGNORECASE) is not None:
        return

    # "Paris,", "[Paris]" 
    place = place.strip(' ()[].,:;')
    place = re.sub( r"^(À|A|En|In|In the|'s|T'|Te) ", '', place, re.IGNORECASE)
    # Madrid, impr. de A. Sanz
    if ',' in place:
        list = place.split(',')
        place = list[0].strip()
        doc_values['publisher'] = list[1].strip()

    # Amsterdam ; et Paris
    # Dresden und Leipzig
    # Londres et Paris
    place = re.sub( r"[  ]?(et|und|;|,).*$", '', place, re.IGNORECASE)
    place = place.strip()
    if not place:
        return
    doc_values['place_group'] = place
    doc_values['place_like'] = bnfmarc.deform(place)


def country(r, doc_values):
    if (r['102'] != None and r['102']['a'] != None):
        doc_values['country'] = r['102']['a']
    # most of old records have no national bib country
    # post work may be done 


def year(r, doc_values):
    str = r['100'].value()[9:13]
    year = str_year(str)
    if (year != None):
        doc_values['year'] = year
        return
    f = None
    if (r['214'] != None):
        f = r['214']
    elif (r['210'] != None):
        f = r['210']
    else: # no other field for date
        return
    year = None
    if (f['d'] != None):
        year = f['d']
    elif (f['r'] != None):
        year = f['r']
    elif doc_values['year'] != None:
        year = doc_values['year']
    else:
        return
    # find [1810]
    found = re.search(r'([\d\?\.]{4})', year)
    if (found == None):
        return
    str = found.group(1)
    year = str_year(str)
    doc_values['year'] = year
    

def str_year(str):
    if (str == None):
        return None
    try:
        year = int(str)
        if year <= year_min or year >= year_max:
            return None
        return year
    except ValueError:
        return None


def docs(marc_file):
    global con
    print("doc < " + marc_file)
    file = os.path.basename(marc_file)
    doc_values = {
        'title': '',
        'desc': None,

        'byline': None,
        'auth1': None,

        'address': None,
        'place': None,
        'place_group': None,
        'place_like': None,
        'publisher': None,
        'publisher_group': None,
        'publisher_like': None,
        'format': None,
        'pages': None,

        'type': None,
        'translation': None,
        'year': None,
        'country': None,
        'clement': None,
        'clement_letter': None,
        'lang': None,

        'file': None,
        'url': '',
        'gallica': None,
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
            url(r, doc_values)
            title(r, doc_values)
            phys(r, doc_values)
            clement(r, doc_values)
            type(r, doc_values)
            lang(r, doc_values)
            address(r, doc_values) # before "place: publisher, year."
            year(r, doc_values)
            publisher(r, doc_values)
            # place after publisher, in case of more precise field
            place(r, doc_values)
            byline(r, doc_values)
            # get first author
            if r['700'] is not None and r['700']['3'] is not None:
                doc_values['auth1'] = auth_id(r['700'])
            elif r['710'] is not None and r['710']['3'] is not None:
                doc_values['auth1'] = auth_id(r['710'])


            # write doc record
            cur.execute(doc_sql, doc_values)
            doc_id = cur.lastrowid
            # link to authors
            auth_links(r, doc_id)



def main() -> int:
    global about_cur, con, contrib_cur, auth_cur
    parser = argparse.ArgumentParser(
        description='Crawl a folder of marc file to generate an sqlite base',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('cataviz_db', nargs=1,
    help='Sqlite database to generate')

    args = parser.parse_args()
    db_file = args.cataviz_db[0]
    con = bnfmarc.connect(db_file)
    auth_cur = con.cursor()
    contrib_cur = con.cursor()
    about_cur = con.cursor()
    marc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/')

    # if (name.startswith('P174_') or name.startswith('P1187_')): 
    for marc_file in glob.glob(os.path.join(marc_dir, "P1187_*.UTF8")):
        docs(marc_file)
    for marc_file in glob.glob(os.path.join(marc_dir, "P174_*.UTF8")):
        docs(marc_file)
    con.commit()

if __name__ == '__main__':
    sys.exit(main())
