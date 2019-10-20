#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
# Name:        importer transakcni historie do sqlite DB souboru aplikace MME MoneyManagerEx
# Author:      P3402617
# Created:     11/01/2016
# Copyright:   (c) P3402617
# -------------------------------------------------------------------------------
import argparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.readers.air_bank import airBankReader
from src.readers.mBank_podnikani_ucet import mBank_podnikani_ucet
from src.readers.mbank_bezny_ucet import mBank_bezny_ucet
from src.readers.rb_bezny_ucet import Raiffeisen_bezny_ucet
from src.readers.rb_card_reader import Raiffeisen_cards
from src.readers.rb_sporici_ucet import Raiffeisen_sporici_ucet
from src.sqlite.sqlalchemy_declarative import Base


class mmx_importer():
    def __init__(self, mmx_sqlite_file, root_dir_trans_hist):
        db_file = f'sqlite:///{mmx_sqlite_file}'
        # engine = create_engine( db_file, echo=True)
        engine = create_engine(db_file)

        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        DBSession.configure(bind=engine)
        session = DBSession()

        # ----------- na��t�n� y CSV do DB
        airBankReader(session, root_dir_trans_hist).read()
        Raiffeisen_cards(session, root_dir_trans_hist).read()
        Raiffeisen_sporici_ucet(session, root_dir_trans_hist).read()
        Raiffeisen_bezny_ucet(session, root_dir_trans_hist).read()
        mBank_bezny_ucet(session, root_dir_trans_hist).read()
        mBank_podnikani_ucet(session, root_dir_trans_hist).read()

        # not exists target account now
        # Anna_ucet_ERA = AnnaUcetEra(session)
        # Anna_ucet_ERA.read()
        # TODO: volat nastaven� kategori� po importu

if __name__ == '__main__':
    # parser and checker for arguments
    parser = argparse.ArgumentParser(
        description='MomenyManagerEx database importer from bank files and category setter')

    parser.add_argument('mmx_sqlite_file', help='path to slite DB file for MMX')
    parser.add_argument('root_dir_trans_hist', help='root directory with transaction history files(CSV from banks)')
    a = parser.parse_args()

    print(a.mmx_sqlite_file)
    mmx_importer(a.mmx_sqlite_file, a.root_dir_trans_hist)
