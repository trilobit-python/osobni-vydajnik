#!/usr/bin/env python
"""
Script to open a sqlite3 database and dump all user tables to CSV files.
Tested in Unicode-rich environment.

Usage:
    dumpsqlite3tocsv foo.db
"""

import os
import os.path
import pandas as pd
import sqlite3


def dump_database_to_spreadsheets(par_file_path):
    db = sqlite3.connect(par_file_path)
    shortname, extension = os.path.splitext(par_file_path)
    os.path.isdir(shortname) or os.mkdir(shortname)
    cursor = db.cursor()
    for table in list_tables(cursor):
        sheetfile = '%s.csv' % table
        sheetpath = os.path.join(shortname, sheetfile)
        dump_table_to_spreadsheet(db, table, sheetpath)



def list_tables(cursor):
    cursor.execute('select name from sqlite_master')
    return [r[0] for r in cursor
            if not r[0].startswith('sqlite')
            and not r[0].startswith('IDX')
            and not r[0].startswith('INDEX')]


def dump_table_to_spreadsheet(db, tablename, sheetpath):
    df = pd.read_sql('select * from %s order by 1' % tablename, db)
    df.to_csv(sheetpath, index=False)
    print(f'Exported {sheetpath}')


if __name__ == '__main__':
    import sys

    for filepath in sys.argv[1:]:
        dump_database_to_spreadsheets(filepath)
