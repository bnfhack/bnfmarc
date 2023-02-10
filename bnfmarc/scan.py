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

def main() -> int:
    parser = argparse.ArgumentParser(
        description='Crawl a folder of marc file to generate an sqlite base',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('marc_file', nargs=1,
    help='A file of MARC records')

    args = parser.parse_args()
    with open(args.marc_file[0], 'rb') as handle:
        reader = pymarc.MARCReader(
            handle, 
            to_unicode=True,
            force_utf8=True
        )
        for r in reader:
            fields = r.get_fields('608')
            if fields is None or len(fields) == 0:
                continue
            i = 0
            for f in fields:
                i = i + 1
                



if __name__ == '__main__':
    sys.exit(main())
