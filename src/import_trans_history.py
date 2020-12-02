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

from src.readers.air_bank import AirBankBeznyUcet, AirBankSporiciUcet
from src.readers.mbank import mBank_bezny_ucet, mBank_podnikani_ucet
from src.readers.raiffeisen import Raiffeisen_cards, Raiffeisen_sporici_ucet, Raiffeisen_bezny_ucet
from src.utils.file import get_backup_filename, copy_file
from src.writer.base_writer import xWriter
from src.writer.kmm_writer import KMMWriter


class TransHistImporter:
    def __init__(self, application, sqlite_file, root_dir_trans_hist):
        self.application = application
        self.sqlite_file = sqlite_file
        self.root_dir_trans_hist = root_dir_trans_hist

    def get_writer(self):
        if self.application == 'mmx':
            return xWriter(self.sqlite_file)
        elif self.application == 'kmm':
            return KMMWriter(self.sqlite_file)
        else:
            raise Exception(f'Unsupported application name{self.application}')

    def set_categories(self):
        self.get_writer().set_categories(self.root_dir_trans_hist)

    def show_rule_candidates(self):
        self.get_writer().show_rule_candidates()

    def set_supertype(self):
        self.get_writer().NastavSuperType()

    def import_csv_files(self):
        readers = [
            # AnnaUcetEra(),
            AirBankBeznyUcet(), AirBankSporiciUcet(),
            mBank_bezny_ucet(), mBank_podnikani_ucet(),
            Raiffeisen_cards(), Raiffeisen_sporici_ucet(), Raiffeisen_bezny_ucet()
        ]
        for reader in readers:
            reader.read(self.root_dir_trans_hist)
            # reader.get_data_frame().to_csv(os.path.join('d:', reader.accName + '.csv'), encoding='cp1250')
            print(reader.accName)
            self.get_writer().zapis_do_db(reader)


if __name__ == '__main__':
    # parser and checker for arguments
    parser = argparse.ArgumentParser(
        description='MomenyManagerEx database importer from bank files and category setter')

    parser.add_argument('application', help='Values mmx=MomenyManagerEx or kmm=KMyMoney',
                        choices=['mmx', 'kmm'], type=str.lower)
    parser.add_argument('sqlite_file', help='path to slite DB file for MMX')
    parser.add_argument('root_dir_trans_hist', help='root directory with transaction history files(CSV from banks)')
    a = parser.parse_args()

    print('Vstupní parametry : ' + str(vars(a)))

    # backup before action, only if different content from previous backup
    path = os.path.dirname(a.sqlite_file)
    backup_file_name = a.sqlite_file.replace(path, os.path.join(path, 'backup'))
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
        # check if same content was backuped
    elif filecmp.cmp(latest_backup_file, a.sqlite_file):
        print(f'Used previous backup Create backup file:{latest_backup_file}')
    else:
        bname = get_backup_filename(backup_file_name)
        print(f'Create backup file:{bname}')
        copy_file(a.sqlite_file, bname)

    # main
    importer = TransHistImporter(a.application, a.sqlite_file, a.root_dir_trans_hist)
    # if False:
    importer.import_csv_files()
    importer.set_categories()
    importer.show_rule_candidates()

    importer.set_supertype()
    print('Done')
