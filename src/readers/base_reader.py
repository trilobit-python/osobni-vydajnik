#!/usr/bin/env python
# -*- coding: windows-1250 -*-

import os.path

from src.utils.file import find_files
from src.sqlite.mmx_db_utils import getACCOUNTID, getPAYEEID
from src.sqlite.sqlalchemy_declarative import CHECKINGACCOUNTV1


class xReader:
    def __init__(self, session, p_accName, root_dir_trans_hist, p_dirSource, p_fileMask):  # konstruktor
        self.ccName = p_accName
        self.dirSource = os.path.join(root_dir_trans_hist, p_dirSource)
        self.fileMask = p_fileMask
        self.session = session
        self.accID = getACCOUNTID(session, p_accName)
        self.PAYEEID = getPAYEEID(session, "None")
        x = getPAYEEID(session, p_accName)
        if x is not None:
            self.PAYEEID = x

    def dej_cislo(self, sCislo):  # vstup ve tvaru 4 952,90
        if sCislo == '':
            return None
        s = sCislo.replace(',', '.')
        s = s.replace(' ', '')
        return float(s)

    def str_float(self, value):
        if isinstance(value, float):
            return value
        return float(value.replace(',', '.').replace(' ', '').replace(u'\xa0', ''))

    def dej_datum_str(self, sDatumStr):  # vstup ve tvaru DD/MM/YYYY
        sOut = f'{sDatumStr[6:10]}-{sDatumStr[3:5]}-{sDatumStr[0:2]}'
        return sOut

    # implementuje potomek
    def import_one_file(self, fname):
        # rozparsuje soubor a ulož transakce do vydaje
        super()

    def read(self):
        # 1. najde všechny soubory v adresářích
        # 2. pro každý soubor provede jeho zpracování - parse a vloření do vydaje
        flist = find_files(self.dirSource, self.fileMask)
        for fnameX in flist:
            print(self.__class__.__name__, fnameX)
            self.import_one_file(fnameX)

    def merge_to_DB(self,
                    ord_num_in_grp,
                    n_exists,
                    xTRANSCODE,
                    xTRANSAMOUNT,
                    xTRANSACTIONNUMBER,
                    xNOTES,
                    xTRANSDATE):

        new_vydaj = CHECKINGACCOUNTV1(
            ACCOUNTID=self.accID,
            TOACCOUNTID=-1,
            PAYEEID=1,
            TRANSCODE=xTRANSCODE,
            TRANSAMOUNT=xTRANSAMOUNT,
            STATUS=self.__class__.__name__,
            TRANSACTIONNUMBER=xTRANSACTIONNUMBER,
            NOTES=xNOTES,
            TRANSDATE=xTRANSDATE,
            FOLLOWUPID=-1,
            TOTRANSAMOUNT=0)

        if n_exists == 0 or n_exists < ord_num_in_grp:
            text: str = 'INS date:{} amount:{} trans:{} note:{}'.format(xTRANSDATE, xTRANSAMOUNT, xTRANSACTIONNUMBER,
                                                                        xNOTES)
            print(self.__class__.__name__, text)
            self.session.add(new_vydaj)
            self.session.flush()
            self.session.commit()
        elif n_exists == 1:
            # OK existuje již právě jeden v DB
            pass
        elif n_exists >= ord_num_in_grp:
            pass
        else:
            # print('Divny stav existuje vice nez 1')
            sKey = xTRANSACTIONNUMBER
            raise Exception(
                'Many records exists[%i] ord_num_in_grp[%i] in DB for key:%s '.format(n_exists, ord_num_in_grp, sKey))
            # kontrola pokud není jednoznačné číslo tranaskace (např. kreditní karty)
            # kontrola dle     datum, castka, ucet, id transakce
