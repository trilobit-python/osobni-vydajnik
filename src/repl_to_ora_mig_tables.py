#!/usr/bin/env python
"""
    Script to open a sqlite3 database and dump all user tables to CSV files.

Usage:
    dumpsqlite3tocsv foo.db
"""

import datetime
import logging
import sys
import pandas as pd

from src.oracle.oracle_database import OracleDatabase
from src.sqlite.sqlite_database import SqliteDatabase
from src.utils.common import  print_frame

def xprint(arg):
    logging.info(arg)


def sqlite2oracle(sqlite_file_name, oracle_conn_str, oracle_schema, migr_tables):
    db_sqlite = SqliteDatabase(sqlite_file_name)
    db_oracle = OracleDatabase(oracle_conn_str)
    for index, row in db_sqlite.list_tables().iterrows():
        table = row['name']
        if table in migr_tables:
            migrate_table(db_sqlite, db_oracle, table, oracle_schema)


def migrate_table(db_sqlite, db_oracle, tablename, oracle_schema):
    target_table = f'MIG_{tablename}'
    xprint(f'Migrate table {tablename} to {oracle_schema}.{target_table}')
    sql_query = f'select * from {tablename} order by 1, 2'
    df_data = db_sqlite.query(sql_query)
    xprint(f'{tablename} num_rows:{df_data.__len__()}')

    df_definition = db_sqlite.get_table_ddl(tablename)
    xprint(df_definition)
    print_frame(pd, df_definition)
    # pd.set_option('display.max_columns', 500)
    # pd.set_option('display.width', 1000)
    db_oracle.drop_if_exists(oracle_schema, target_table, 'TABLE')
    xprint(f'create from sqlite ddl')
    xprint(f'insert data from df to target')


if __name__ == '__main__':
    logging.basicConfig(
        filename=f"{__name__}_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.log",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format='%(message)s'
    )
    logging.getLogger().addHandler(logging.StreamHandler())

    oracle_conn_str = f'sys/sys@orcl'
    migr_tables = ['ACCOUNTLIST_V1']

    for sqlite_file_name in sys.argv[1:]:
        sqlite2oracle(sqlite_file_name, oracle_conn_str, 'vydaje', migr_tables)
