#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
# Name:        importer transakcni historie do sqlite DB souboru aplikace MME MoneyManagerEx
# Author:      P3402617
# Created:     11/01/2016
# Copyright:   (c) P3402617
# -------------------------------------------------------------------------------
import argparse

import pandas
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.category_setter.category_setter import CategorySetter
from src.readers.air_bank import airBankReader
from src.readers.mBank_podnikani_ucet import mBank_podnikani_ucet
from src.readers.mbank_bezny_ucet import mBank_bezny_ucet
from src.readers.rb_bezny_ucet import Raiffeisen_bezny_ucet
from src.readers.rb_card_reader import Raiffeisen_cards
from src.readers.rb_sporici_ucet import Raiffeisen_sporici_ucet
from src.sqlite.sqlalchemy_declarative import Base
from src.sqlite.sqlite_database import SqliteDatabase
from src.utils.common import print_frame
from src.utils.file import get_backup_filename, copy_file


class MoneyManagerImporter:
    def __init__(self, mmx_sqlite_file):
        self.mmx_sqlite_file = mmx_sqlite_file
        self._db_file = f'sqlite:///{mmx_sqlite_file}'
        # engine = create_engine( db_file, echo=True)
        engine = create_engine(self._db_file)

        Base.metadata.bind = engine
        session = sessionmaker(bind=engine)
        session.configure(bind=engine)
        self.session = session()

    def import_csv_files(self, root_dir_trans_hist):
        # ----------- načítání y CSV do DB
        airBankReader(self.session, root_dir_trans_hist).read()
        Raiffeisen_cards(self.session, root_dir_trans_hist).read()
        Raiffeisen_sporici_ucet(self.session, root_dir_trans_hist).read()
        Raiffeisen_bezny_ucet(self.session, root_dir_trans_hist).read()
        mBank_bezny_ucet(self.session, root_dir_trans_hist).read()
        mBank_podnikani_ucet(self.session, root_dir_trans_hist).read()

    def set_categ_by_rules(self):
        # not exists target account now
        # Anna_ucet_ERA = AnnaUcetEra(session)
        # Anna_ucet_ERA.read()
        # TODO: volat nastavení kategorií po importu
        print('TODO: volat nastavení kategorií po importu')
        setter = CategorySetter
        setter.set_categories(self.mmx_sqlite_file)

    def show_rule_candidates(self):
        db_sqlite = SqliteDatabase(self.mmx_sqlite_file)
        result = db_sqlite.query('''SELECT NOTES, Pocet, SumCastka, MinDate, MaxDate 
                                   from v_statistika_bez_kategorie
                                     where pocet > 1
                                     order by pocet desc''')
        print_frame(pandas, result)


if __name__ == '__main__':
    # parser and checker for arguments
    parser = argparse.ArgumentParser(
        description='MomenyManagerEx database importer from bank files and category setter')

    parser.add_argument('mmx_sqlite_file', help='path to slite DB file for MMX')
    parser.add_argument('root_dir_trans_hist', help='root directory with transaction history files(CSV from banks)')
    a = parser.parse_args()

    print(a.mmx_sqlite_file)

    # backup before action
    bname = get_backup_filename(a.mmx_sqlite_file)
    print(f'Create backup file:{bname}')
    copy_file(a.mmx_sqlite_file, bname)

    # main
    importer = MoneyManagerImporter(a.mmx_sqlite_file)
    importer.import_csv_files(a.root_dir_trans_hist)
    importer.set_categ_by_rules()
    importer.show_rule_candidates()
