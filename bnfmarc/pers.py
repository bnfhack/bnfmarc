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

# shared sqlite3 connexion
con = None

def records(marc_file):
    global con
    print(marc_file)

    pers_row = {
        'file': None,
        'url': None,
        'nb': None,
        'name': None,
        'given': None,
        'role': None,
        'birthyear': None,
        'deathyear': None,
        'birthplace': None,
        'deathplace': None,
    }
    pers_sql = "INSERT INTO doc (" + ", ".join([*pers_row]) + ") VALUES (:" + ", :".join([*pers_row]) +")"
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

            for key in pers_row:
                pers_row[key] = None
            pers_row['file'] = os.path.basename(marc_file)
            pers_row['url'] = str(r['003'].value())
            #  http://catalogue.bnf.fr/ark:/12148/cb15037139g
            nb = str(r['003']).split('ark:/12148/cb')[1]
            nb = nb[:-1] # id verified, is unique
            pers_row['nb'] = int(nb)
            if (r['200'] is not None): # a pers
                if (r['200']['a'] is None): # 1 found with no name
                    continue
                pers_row['name'] = r['200']['a']
                pers_row['given'] = r['200']['b']
                pers_row['role'] = r['200']['c']
                dates(r, pers_row)

                if (r['301'] is not None):
                    if (r['301']['a'] is not None):
                         pers_row['birthplace'] = r['301']['a']
                    if (r['301']['a'] is not None):
                         pers_row['deathplace'] = r['301']['a']


            if (r['210'] is not None): # an org
                continue
            else:
                continue


            # cur.execute(pers_sql, pers_row)

def dates(r, pers_row):
    # dates 
    if (r['200']['f'] is not None):
        dateline = r['200']['f']
        sign = 1
        if dateline.find('av.') > -1:
            sign = -1
        res = re.search('^[^\-\d]*(\d\d\d\d)', dateline)
        if res is not None:
            pers_row['birthyear'] = sign * int(res.group(1))
        res = re.search('\-[^\d]*(\d\d\d\d)', dateline)
        if res is not None:
            pers_row['deathyear'] =  sign * int(res.group(1))
    # check age
    if pers_row['birthyear'] is not None and pers_row['deathyear'] is not None:
        pers_row['age'] = pers_row['deathyear'] - pers_row['birthyear']
        if pers_row['age'] > 1 and pers_row['age'] < 120:
            return
    # try better ?    
    if (r['103'] is not None and r['103']['a'] is not None):
        dateline = r['103']['a']
        # birth
        pers_row['birthyear'] = dateline[0:5].strip()
        if re.search(r'^\-?[\d ]+$', pers_row['birthyear']) is None:
            pers_row['birthyear'] = None
        else:
            pers_row['birthyear'] = int(pers_row['birthyear'])
        # death
        pers_row['deathyear'] = dateline[10:15].strip()
        if re.search(r'^\-?[\d ]+$', pers_row['deathyear']) is None:
            pers_row['deathyear'] = None
        else: 
            try:
                pers_row['deathyear'] = int(pers_row['deathyear'])
            except:
                print('"' + pers_row['deathyear'] + '"')
                print(r)

    # age at death
    if pers_row['birthyear'] is not None and pers_row['deathyear'] is not None:
        pers_row['age'] = pers_row['deathyear'] - pers_row['birthyear']
        if pers_row['age'] > 10 and pers_row['age'] < 120:
            return
        # age impossible
        pers_row['birthyear'] = None
        pers_row['deathyear'] = None
        pers_row['age'] = None




def main() -> int:
    global con
    parser = argparse.ArgumentParser(
        description='Crawl a folder of marc authority records to populate an sqlite base',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('cataviz_db', nargs=1,
    help='Sqlite database to generate')
    args = parser.parse_args()
    con = bnfmarc.connect(args.cataviz_db[0])
    marc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/')
    for marc_file in glob.glob(os.path.join(marc_dir, "P1486_*.UTF8")):
        records(marc_file)
    con.commit()

if __name__ == '__main__':
    sys.exit(main())
