"""
Part of bnfmarc https://github.com/bnfhack/bnfmarc
Copyright (c) 2022 frederic.glorieux@fictif.org
MIT License https://opensource.org/licenses/mit-license.php
Code policy PEP8 https://www.python.org/dev/peps/pep-0008/
"""


"""
Load authority records, especially, persons.
Doc: https://www.bnf.fr/sites/default/files/2019-01/UNIMARC%28A%29_2018_conversion.pdf
Data : https://api.bnf.fr/notices-dautorite-personnes-collectivites-oeuvres-lieux-noms-communs-de-bnf-catalogue-general
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
pers_nb = {}
pers_row = {
    'nb': None,
    'name': None,
    'given': None,
    'gender': None,
    'deform': None,

    'birthyear': None,
    'deathyear': None,
    'age': None,
}
pers_sql = "INSERT INTO pers (" + ", ".join([*pers_row]) + ") VALUES (:" + ", :".join([*pers_row]) +")"


def byline(doc_file):
    global pers_row
    print(doc_file)
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
            # loop on personal responsabilities
            for field in r.get_fields('700'):
                byline_field(cur, field)
            for field in r.get_fields('701'):
                byline_field(cur, field)
            for field in r.get_fields('702'):
                byline_field(cur, field)
            for field in r.get_fields('703'):
                byline_field(cur, field)
            

def byline_field(cur, field):
    global pers_nb, pers_sql, pers_row
    if (field['3'] is None):
        # ~10 cases found
        return
    nb = int(field['3'])
    if nb in pers_nb:
        # already written
        return
    # a link to id only is possible
    if field['a'] is None:
        return
    # clean record
    for key in pers_row:
        pers_row[key] = None
    pers_row['nb'] = nb
    # extract names
    names(field, pers_row)
    pers_row['gender'] = gender_given(pers_row['given'])
    # extract dates
    dateline(field['f'], pers_row)
    # keep id
    pers_nb[nb] = True
    cur.execute(pers_sql, pers_row)



def auths(marc_file):
    global con, pers_nb
    print(marc_file)

    pers_row = {
        'file': None,
        'url': None,
        'nb': None,
        'name': None,
        'given': None,
        'gender': None,
        'role': None,
        'deform': None,

        'birthyear': None,
        'deathyear': None,
        'age': None,
        'birthplace': None,
        'deathplace': None,
    }
    pers_sql = "INSERT INTO pers (" + ", ".join([*pers_row]) + ") VALUES (:" + ", :".join([*pers_row]) +")"
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
            for key in pers_row:
                pers_row[key] = None

            pers_row['file'] = os.path.basename(marc_file)
            pers_row['url'] = str(r['003'].value().strip())
            #  http://catalogue.bnf.fr/ark:/12148/cb15037139g
            nb = str(r['003']).split('ark:/12148/cb')[1]
            nb = nb[:-1] # id verified, is unique
            pers_row['nb'] = int(nb)
            if (r['200'] is not None): # a pers
                if (r['200']['a'] is None): # 1 found with no name
                    continue
                # get names from field
                names(r['200'], pers_row)
                dates(r, pers_row)

                if (r['301'] is not None):
                    if (r['301']['a'] is not None):
                         pers_row['birthplace'] = r['301']['a'].strip()
                    if (r['301']['b'] is not None):
                         pers_row['deathplace'] = r['301']['b'].strip()
                gender(r, pers_row)
                # keep id in mem
                pers_nb[pers_row['nb']] = True
                # write a person
                cur.execute(pers_sql, pers_row)

            if (r['210'] is not None): # an org
                continue
            else:
                continue


def names(field, pers_row):
    """
    Extract person names from a pymarc field to populate a pers row.
    Field = auth#200 or doc#700

    """
    if field['a'] is None:
        return
    pers_row['name'] = field['a'].strip()

    if (field['b'] is not None):
        pers_row['given'] = field['b'].strip()
        pers_row['deform'] = pers_row['name'] + ", " + pers_row['given']
    else:
        pers_row['deform'] = pers_row['name']
    # for search, low case without diacritics
    pers_row['deform'] = bnfmarc.deform(pers_row['deform'])

    if (field['c'] is not None):
        pers_row['role'] = field['c'].strip()

def gender(r, pers_row):
    if (r['120'] is not None and r['120']['a'] is not None):
        if r['120']['a'] == 'b':
            pers_row['gender'] = 1
            return
        elif r['120']['a'] == 'a':
            pers_row['gender'] = 2
            return
    pers_row['gender'] = gender_given(pers_row['given'])

def gender_given(given):
    """Get a gender from a given name"""
    if given is None:
        return None
    given = re.split(' |-', given.casefold())[0]
    return givens.dic.get(given, None)

def dateline(dateline, pers_row):
    if (dateline is None):
        return
    sign = 1
    if dateline.find('av.') > -1:
        sign = -1
    res = re.search('^[^\-\d]*(\d\d\d\d)', dateline)
    if res is not None:
        pers_row['birthyear'] = sign * int(res.group(1))
    res = re.search('\-[^\d]*(\d\d\d\d)', dateline)
    if res is not None:
        pers_row['deathyear'] =  sign * int(res.group(1))
    # check age at death
    age(pers_row)
    
def age(pers_row):
    if pers_row['birthyear'] is None or pers_row['deathyear'] is None:
        return
    age = pers_row['deathyear'] - pers_row['birthyear']
    if age > 10 or age < 120:
        # age possible
        pers_row['age'] = age
        return
    # 1 or 2 dates are bad
    pers_row['birthyear'] = None
    pers_row['deathyear'] = None
    return



def dates(r, pers_row):
    # reord dateline
    dateline(r['200']['f'], pers_row)
    # good job done, bye
    if pers_row['age'] is not None:
        return
    # nothing better to find    
    if r['103'] is None or r['103']['a'] is None:
        return
    # try better ?    
    line = r['103']['a']
    # birth
    birthyear = line[0:5].strip()
    if re.search(r'^\-?[\d ]+$', birthyear) is not None:
        pers_row['birthyear'] = int(birthyear)
    # death
    deathyear = line[10:15].strip()
    if re.search(r'^\-?[\d ]+$', deathyear) is not None:
        pers_row['deathyear'] = int(deathyear)
    age(pers_row)




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
