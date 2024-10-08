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
        description='Scan a marc file',
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
            url = r['003'].value()
            if (url != 'http://catalogue.bnf.fr/ark:/12148/cb30047888b'):
                continue
            print(r)


if __name__ == '__main__':
    sys.exit(main())
