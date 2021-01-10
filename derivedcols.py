#!/usr/bin/env python3
'''
Compute derived columns in a metadata table
'''

import argparse
import csv

class Adder_Table_Map:
    def __init__(self, tab_file):
        self._mapper = {}
        self._default_col = None
        with open(tab_file, 'rt') as inf:
            reader = csv.DictReader(inf, delimiter='\t')
            self._col_name = reader.fieldnames[0]
            self._orig_cols = reader.fieldnames[1:]
            for row in reader:
                if all(v=='*' for k,v in row.items() if k in self._orig_cols):
                    self._default_col = row.get(self._col_name)
                else:
                    k = self._make_key_str(row)
                    v = row.get(self._col_name, '')
                    print("setting {}={} if {}".format(self._col_name, v, k))
                    self._mapper[k] = v
    def _make_key_str(self, row):
        key_str = ':'.join('='.join((k,row.get(k,''))) for k in self._orig_cols)
        return key_str
    def extra_headers(self):
        return (self._col_name,)
    def modify_row(self, row):
        k = self._make_key_str(row)
        v = self._mapper.get(k)
        if v is None and self._default_col:
           v = row.get(self._default_col, '')
        row[self._col_name] = v
        return row

class Adder_Source_Lab_Subset:
    def __init__(self, restrict_string):
        self._prefix = restrict_string.split(';')[0]
        self._restrict_map = dict(kv.split('=') for kv in restrict_string.split(';')[1].split(':'))
    def extra_headers(self):
        return (self._prefix + '_originating_lab', self._prefix + '_submitting_lab')
    def modify_row(self, row):
        if all((row.get(k) == v) for k,v in self._restrict_map.items()):
            row[self._prefix + '_originating_lab'] = row['originating_lab']
            row[self._prefix + '_submitting_lab']  = row['submitting_lab']
        return row

def add_derived_cols(in_tsv, out_tsv, table_maps=None, lab_highlight_loc=None):
    adders = []
    if not table_maps:
        table_maps = ()
    for t in table_maps:
        adders.append(Adder_Table_Map(t))
    if lab_highlight_loc:
       adders.append(Adder_Source_Lab_Subset(lab_highlight_loc))

    with open(in_tsv, 'rt') as inf:
        reader = csv.DictReader(inf, delimiter='\t')
        out_headers = reader.fieldnames
        for adder in adders:
            out_headers.extend(adder.extra_headers())

        with open(out_tsv, 'wt') as outf:
            writer = csv.DictWriter(outf, out_headers, delimiter='\t')
            writer.writeheader()
            for row in reader:
                for adder in adders:
                    adder.modify_row(row)
                writer.writerow(row)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="modify metadata table to compute derivative columns on the fly and add or replace new columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("in_tsv",  type=str, help="input metadata")
    parser.add_argument("out_tsv", type=str, help="output metadata")
    parser.add_argument("--table_map", type=str, nargs='*', help="mapping table")
    parser.add_argument("--lab_highlight_loc", type=str, help="call out source labs")
    args = parser.parse_args()
    add_derived_cols(args.in_tsv, args.out_tsv, table_maps=args.table_map, lab_highlight_loc=args.lab_highlight_loc)
