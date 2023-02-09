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
            fields = r.get_fields('930')
            if fields is None or len(fields) == 0:
                # > 1970
                continue
            i = 0
            for f in r.get_fields('930'):
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
                        print(cote + "|" + str(f))
                    clement_format(found.group('format'), cote)
                    #
                    continue
                # THETA ?
                found = re.search(r"(FR-\d{9}):([A-Z]+ )?((?P<format>[^\-]+)-)(?P<clement>THETA|TH)", cote)
                if found is not None:
                    clement_format(found.group('format'), cote)
                    continue
                """
                if found.group('format') is not None:
                    print (str(i) + ' ' + found.group('format') + " " + cote)
                """

def clement_format(format, doc_values):
    if format is None or format == '':
        return
    if format == 'FOL':
        format = '2'
    if not format.isdigit():
        return
    # doc_values['format'] = int(format)


if __name__ == '__main__':
    sys.exit(main())
