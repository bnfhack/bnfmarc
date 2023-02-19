"""
Part of bnfmarc https://github.com/bnfhack/bnfmarc
Copyright (c) 2022 frederic.glorieux@fictif.org
MIT License https://opensource.org/licenses/mit-license.php
Code policy PEP8 https://www.python.org/dev/peps/pep-0008/
"""


"""
Load authority records, especially, authons.
Doc: https://www.bnf.fr/sites/default/files/2019-01/UNIMARC%28A%29_2018_conversion.pdf
Data : https://api.bnf.fr/notices-dautorite-authonnes-collectivites-oeuvres-lieux-noms-communs-de-bnf-catalogue-general
ftp://PRODUIT_RETRO:b9rZ2As7@pef.bnf.fr/PRODUIT_RETRO/Pcts/Pcts_2021/Pcts_2021_Unimarc_UTF8/P1486_*.UTF8
"""
import argparse
import glob
import os
import pymarc
import re
import sqlite3
import sys

# local
import bnfmarc
import givens

# shared sqlite3 connexion
con = None
# mem ids 
auth_cache = {}
auth_row = {
    'id': None,
    'type': None,
    'name': None,
    'deform': None,
    'role': None,

    'given': None,
    'gender': None,
    'birthyear': None,
    'deathyear': None,
    'age': None,
}
auth_sql = "INSERT INTO auth (" + ", ".join([*auth_row]) + ") VALUES (:" + ", :".join([*auth_row]) +")"


def byline(doc_file):
    global auth_row
    print("auth < " + doc_file)
    cur = con.cursor()
    with open(doc_file, 'rb') as handle:
        reader = pymarc.MARCReader(
            handle, 
            to_unicode=True,
            force_utf8=True
        )
        for r in reader:
            if (r is None): # some found, forget
                continue
            # loop on authonal responsabilities
            for field in r.get_fields('700'):
                auth_indoc(cur, field, type=1)
            for field in r.get_fields('701'):
                auth_indoc(cur, field, type=1)
            for field in r.get_fields('702'):
                auth_indoc(cur, field, type=1)
            for field in r.get_fields('703'):
                auth_indoc(cur, field, type=1)
            # person as a subject
            for field in r.get_fields('600'):
                auth_indoc(cur, field, type=1)

            # loop on corporate resonsabilities
            for field in r.get_fields('710'):
                auth_indoc(cur, field, type=2)
            for field in r.get_fields('711'):
                auth_indoc(cur, field, type=2)
            for field in r.get_fields('712'):
                auth_indoc(cur, field, type=2)
            for field in r.get_fields('713'):
                auth_indoc(cur, field, type=2)
            # corporate as a subject
            for field in r.get_fields('601'):
                auth_indoc(cur, field, type=2)
            

def auth_indoc(cur, field, type=1):
    global auth_cache, auth_row
    if (field['3'] is None):
        # ~10 cases found
        return
    # found 3 cases with nb repetition
    id = int(field['3'][0:8])
    if id in auth_cache:
        # already written
        return
    # a link to id only is possible
    if field['a'] is None:
        return
    # clean record
    for key in auth_row:
        auth_row[key] = None
    auth_row['id'] = id
    auth_row['type'] = type
    if type == 1:
        # extract names
        pers_names(field, auth_row)
        auth_row['gender'] = gender_given(auth_row['given'])
        # extract dates
        dateline(field['f'], auth_row)
    elif type == 2:
        corp_name(field, auth_row)
    # keep id
    auth_cache[id] = True
    cur.execute(auth_sql, auth_row)



def auths(marc_file):
    global con, auth_cache
    print("auth < " + marc_file)

    auth_row = {
        'id': None,
        'type': None,
        'name': None,
        'role': None,
        'deform': None,

        'note': None,


        'given': None,
        'gender': None,
        'birthyear': None,
        'deathyear': None,
        'age': None,
        'birthplace': None,
        'deathplace': None,

        'file': None,
        'url': None,
    }
    auth_sql = "INSERT INTO auth (" + ", ".join([*auth_row]) + ") VALUES (:" + ", :".join([*auth_row]) +")"
    cur = con.cursor()
    with open(marc_file, 'rb') as handle:
        reader = pymarc.MARCReader(
            handle, 
            to_unicode=True,
            force_utf8=True
        )
        for r in reader:
            if (r is None): # 2 founds, forget
                continue
            if (r['003'] is None): # never found
                continue
            # nonify data to write to sqlite
            for key in auth_row:
                auth_row[key] = None

            auth_row['file'] = os.path.basename(marc_file)
            auth_row['url'] = str(r['003'].value().strip())
            #  http://catalogue.bnf.fr/ark:/12148/cb15037139g
            id = str(r['003']).split('ark:/12148/cb')[1]
            id = id[0:8] # id verified, is unique
            auth_row['id'] = int(id)
            # informative note
            if (r['300'] is not None and r['300']['a'] is not None):
                auth_row['note'] = str(r['300']['a'].strip())
            if (r['200'] is not None): # a pers
                if (r['200']['a'] is None): # 1 found with no name
                    continue
                auth_row['type'] = 1
                # get names from field
                pers_names(r['200'], auth_row)
                pers_dates(r, auth_row)

                if (r['301'] is not None):
                    if (r['301']['a'] is not None):
                         auth_row['birthplace'] = str(r['301']['a'].strip())
                    if (r['301']['b'] is not None):
                         auth_row['deathplace'] = str(r['301']['b'].strip())
                gender(r, auth_row)
                # keep id in mem
                auth_cache[auth_row['id']] = True
                # write a authon
                cur.execute(auth_sql, auth_row)

            if (r['210'] is not None): # a corp
                auth_row['type'] = 2
                corp_name(r['210'], auth_row)
                continue
            else:
                continue

def corp_name(field, auth_row):
    if field['a'] is None:
        return
    name =  field['a'].strip()
    if field['b'] is not None:
        name = name + ', ' + field['b'].strip()
    if (field['c'] is not None):
        auth_row['role'] = field['c'].strip()
    auth_row['name'] = name
    auth_row['deform'] = bnfmarc.deform(name)


def pers_names(field, auth_row):
    """
    Extract authon names from a pymarc field to populate a auth row.
    Field = auth#200 or doc#700

    """
    if field['a'] is None:
        return
    auth_row['name'] = field['a'].strip()
    deform = auth_row['name']
        
    if (field['b'] is not None):
        auth_row['given'] = field['b'].strip()
        deform = deform + ", " + auth_row['given']

    # kings, emperors
    if (field['d'] is not None):
        auth_row['name'] = auth_row['name'] + ' ' + field['d'].strip()
        deform = deform + " " + field['d'].strip()

    # for search, low case without diacritics
    auth_row['deform'] = bnfmarc.deform(deform)

    if (field['c'] is not None):
        auth_row['role'] = field['c'].strip()

def gender(r, auth_row):
    if (r['120'] is not None and r['120']['a'] is not None):
        if r['120']['a'] == 'b':
            auth_row['gender'] = 1
            return
        elif r['120']['a'] == 'a':
            auth_row['gender'] = 2
            return
    auth_row['gender'] = gender_given(auth_row['given'])

def gender_given(given):
    """Get a gender from a given name"""
    if given is None:
        return None
    given = re.split(' |-', given.casefold())[0]
    return givens.dic.get(given, None)

def dateline(dateline, auth_row):
    if (dateline is None):
        return
    sign = 1
    if dateline.find('av.') > -1:
        sign = -1
    res = re.search('^[^\-\d]*(\d\d\d\d)', dateline)
    if res is not None:
        auth_row['birthyear'] = sign * int(res.group(1))
    res = re.search('\-[^\d]*(\d\d\d\d)', dateline)
    if res is not None:
        auth_row['deathyear'] =  sign * int(res.group(1))
    # check age at death
    age(auth_row)
    
def age(auth_row):
    if auth_row['birthyear'] is None or auth_row['deathyear'] is None:
        return
    age = auth_row['deathyear'] - auth_row['birthyear']
    if age > 10 or age < 120:
        # age possible
        auth_row['age'] = age
        return
    # 1 or 2 dates are bad
    auth_row['birthyear'] = None
    auth_row['deathyear'] = None
    return



def pers_dates(r, auth_row):
    # reord dateline
    dateline(r['200']['f'], auth_row)
    # good job done, bye
    if auth_row['age'] is not None:
        return
    # nothing better to find    
    if r['103'] is None or r['103']['a'] is None:
        return
    # try better ?    
    line = r['103']['a']
    # birth
    birthyear = line[0:5].strip()
    if re.search(r'^\-?[\d ]+$', birthyear) is not None:
        auth_row['birthyear'] = int(birthyear)
    # death
    deathyear = line[10:15].strip()
    if re.search(r'^\-?[\d ]+$', deathyear) is not None:
        auth_row['deathyear'] = int(deathyear)
    age(auth_row)




def main() -> int:
    global con
    parser = argparse.ArgumentParser(
        description='Crawl a folder of marc authority records to populate an sqlite base',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('cataviz_db', nargs=1,
    help='Sqlite database to generate')
    args = parser.parse_args()
    con = bnfmarc.connect(args.cataviz_db[0], True)
    marc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/')
    
    # loop on auth record
    for auth_file in glob.glob(os.path.join(marc_dir, "P1486_*.UTF8")):
        auths(auth_file)
    con.commit()
    # add authors from document records but without authority
    for doc_file in glob.glob(os.path.join(marc_dir, "P1187_*.UTF8")):
        byline(doc_file)
    con.commit()
    for doc_file in glob.glob(os.path.join(marc_dir, "P174_*.UTF8")):
        byline(doc_file)
    con.commit()

if __name__ == '__main__':
    sys.exit(main())
