#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
# Name:        importer transakcni historie do sqlite DB souboru aplikace MME MoneyManagerEx
# Author:      P3402617
# Created:     11/01/2016
# Copyright:   (c) P3402617
# -------------------------------------------------------------------------------
import argparse
import filecmp
import glob
import os
import sqlite3
import sys


import numpy as np

from src.readers import AirBankBeznyUcet, AirBankSporiciUcet
from src.readers import MBankBeznyUcet, mBank_podnikani_ucet
from src.readers import Raiffeisen_cards, Raiffeisen_sporici_ucet, Raiffeisen_bezny_ucet
from src.utils import get_backup_filename, copy_file
from src.utils import SqliteDatabase
from src.writer import Writer


class TransHistImporter:
    def __init__(self, p_sqlite_file, p_root_dir_trans_hist):
        self.sqlite_file = p_sqlite_file
        self.root_dir_trans_hist = p_root_dir_trans_hist
        self.db = SqliteDatabase(p_sqlite_file)
        #  TODO: přejít na SqlAlchemy - ORM
        # from sqlalchemy import MetaData, create_engine
        #
        # CONN = create_engine(DB_URL, client_encoding="UTF-8")
        #
        # META_DATA = MetaData(bind=CONN, reflect=True)
        #
        # USERS_TABLE = META_DATA.tables['users']
        #
        self.writer = Writer(self.db)

    def __del__(self):
        pass

    def __enter__(self):
        # Integer in python/pandas becomes BLOB (binary) in sqlite
        sqlite3.register_adapter(np.int64, lambda val: int(val))
        sqlite3.register_adapter(np.int32, lambda val: int(val))
        try:
            self.conn = sqlite3.connect(self.sqlite_file)
        except sqlite3.Error:
            raise ValueError(f'Failed to connect to database! {sqlite3.Error}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.rollback()
            self.conn.close()

    def import_csv_files(self):
        readers = [
            # AnnaUcetEra(),
            AirBankBeznyUcet(), AirBankSporiciUcet(),
            MBankBeznyUcet(), mBank_podnikani_ucet(),
            Raiffeisen_cards(), Raiffeisen_sporici_ucet(), Raiffeisen_bezny_ucet()
        ]
        for reader in readers:
            reader.read(self.root_dir_trans_hist)
            print(reader.accName)
            self.writer.zapis_do_db(reader)

    def backup_before_all(self):
        # backup before action, only if different content from previous backup
        path = os.path.dirname(self.sqlite_file)
        backup_file_name = self.sqlite_file.replace(path, os.path.join(path, 'backup'))
        bkp_file_pattern = backup_file_name + '.*.bkp'
        print(bkp_file_pattern)
        bkp_files = glob.glob(bkp_file_pattern)
        latest_backup_file = None
        if bkp_files:
            latest_backup_file = max(bkp_files, key=os.path.getctime)
        if not latest_backup_file:
            bname = get_backup_filename(backup_file_name)
            print(f'Create brand new backup file:{bname}')
            copy_file(a.sqlite_file, bname)
            # check if same content was backed
        elif filecmp.cmp(latest_backup_file, a.sqlite_file):
            print(f'Used previous backup Create backup file:{latest_backup_file}')
        else:
            bname = get_backup_filename(backup_file_name)
            print(f'Create backup file:{bname}')
            copy_file(a.sqlite_file, bname)

    def main(self):
        self.backup_before_all()
        self.import_csv_files()
        self.writer.set_categories(self.root_dir_trans_hist)
        self.writer.show_rule_candidates()
        self.writer.prenastav_supertype()


if __name__ == '__main__':
    PROJECT_ROOT = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.pardir)
    )
    sys.path.append(PROJECT_ROOT)

    # argumenty příkazového řádku
    parser = argparse.ArgumentParser(description='MomenyManagerEx database importer from bank files and category set')
    parser.add_argument('sqlite_file', help='path to slite DB file for MMX')
    parser.add_argument('root_dir_trans_hist', help='root directory with transaction history files(CSV from banks)')
    a = parser.parse_args()

    print('Vstupní parametry : ' + str(vars(a)))

    with TransHistImporter(a.sqlite_file, a.root_dir_trans_hist) as importer:
        importer.main()

    print('Done')
