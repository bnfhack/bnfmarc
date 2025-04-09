"""
Part of bnfmarc https://github.com/bnfhack/bnfmarc
Copyright (c) 2022 frederic.glorieux@fictif.org
MIT License https://opensource.org/licenses/mit-license.php
Code policy PEP8 https://www.python.org/dev/peps/pep-0008/
"""

import argparse
import pymarc
import re
import sys

def docs(marc_file):
    print(marc_file)

def year(r):
    str = r.get('100').value()[9:13]
    year = str_year(str)
    if (year != None):
        doc_values['year'] = year
        return
    f = None
    if (r.get('214') != None):
        f = r.get('214')
    elif (r.get('210') != None):
        f = r.get('210')
    else: # no other field for date
        return
    year = None
    if (f.get('d') != None):
        year = f.get('d')
    elif (f.get('r') != None):
        year = f.get('r')
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



def main() -> int:
    for marc_file in glob.glob(os.path.join(marc_dir, "P174_*.UTF8")):
        search(marc_file)



if __name__ == '__main__':
    sys.exit(main())
