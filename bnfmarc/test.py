"""
Part of bnfmarc https://github.com/bnfhack/bnfmarc
Copyright (c) 2022 frederic.glorieux@fictif.org
MIT License https://opensource.org/licenses/mit-license.php
Code policy PEP8 https://www.python.org/dev/peps/pep-0008/
"""

import argparse
import glob
import pymarc
import os
import re
import sys



# big dic of url
years = {}

def walk(marc_dir):
    """Parse marc files"""
    if not os.path.isdir(marc_dir):
        raise Exception("Dir not found for marc data:\"" + marc_dir + "\"")
    for root, dirs, files in os.walk(marc_dir):
        for name in files:
            if (not name.startswith('P174')):
                continue
            marc_file = os.path.join(root, name)
            print(marc_file)
            parse(marc_file)
            for k, v in years.items(): 
                print(k, v)

def parse(marc_file):
    global year_min, year_max
    pat = re.compile(r'(\-?[\d\?\.]+)')
    with open(marc_file, 'rb') as handle:
        reader = pymarc.MARCReader(
            handle, 
            to_unicode=True,
            force_utf8=True
        )
        for r in reader:
            if (r['003'] == None):
                print("NO 003")
                print(r)
                continue
            if (r['008'] == None):
                # print("NO 008")
                # print(r)
                continue
            date = r['008'].value()[8:12]
            year = str_year(date)
            if (year == None and not r['260']):
                date = r['260']['d']
                if (date == None):
                    continue
                res = pat.search(date)
                if (res == None):
                    continue
                date = res.group(1)
            year = str_year(date)
            if (year == None):
                continue
            years[year] = years.setdefault(year, 0) + 1
            """
            if (r['051'] == None):
                for f in r.get_fields('003'):
                    url = 'http://catalogue.bnf.fr/ark:/12148/cb301683267'
                    print(f.value() == url)
            """
            # print (r['000'])
            # print(r['051'])

def str_year(str):
    if (str == None):
        return None
    try:
        year = int(str)
        return year
    except ValueError:
        return None

def main() -> int:
    parser = argparse.ArgumentParser(
        description='Crawl a folder of marc file to test pymarc',
        formatter_class=argparse.RawTextHelpFormatter
    )
    args = parser.parse_args()
    marc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/')
    walk(marc_dir)

if __name__ == '__main__':
    sys.exit(main())
