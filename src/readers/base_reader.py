#!/usr/bin/env python
# -*- coding: windows-1250 -*-

import os.path

import numpy
import pandas

from src.utils.file import find_files


class xReader:
    def __init__(self):
        self.dictinary_list = []
        self.accName = None

    def __len__(self):
        return len(self.dictinary_list)

    def add_row(self,
                transcode: str,
                transamount: float,
                transactionnumber: str,
                note: str,
                date: numpy.datetime64,
                payee: str):

        row = [date, transamount, note, transcode, transactionnumber, payee]
        self.dictinary_list.append(row)

    def get_data_frame(self):
        df = pandas.DataFrame.from_dict(self.dictinary_list)
        df.drop_duplicates(inplace=True)
        df.columns = ['Datum',
                      'Částka',
                      'Poznámka',
                      'Operace',
                      'ID transakce',
                      'Plátce/Příjemce']
        df.sort_values(['Datum', 'Částka'], inplace=True)
        return df

    @staticmethod
    def dej_cislo(sCislo):  # vstup ve tvaru 4 952,90
        if sCislo == '':
            return None
        s = sCislo.replace(',', '.')
        s = s.replace(' ', '')
        return float(s)

    def str_float(self, value):
        if isinstance(value, float):
            return value
        return float(value.replace(',', '.').replace(' ', '').replace(u'\xa0', ''))

    @staticmethod
    def dej_datum_str(sDatumStr):  # vstup ve tvaru DD/MM/YYYY
        sOut = f'{sDatumStr[6:10]}-{sDatumStr[3:5]}-{sDatumStr[0:2]}'
        return sOut

    def import_one_file(self, fname):
        """ rozparsuje soubor a ulož transakce do vydaje
            implemtuje potomek
        """
        super()

    def read(self, root_dir_trans_hist, acc_name, dir_source, file_mask):
        """ TODO dodělat pořádný popis
            1. najde všechny soubory v adresářích
            2. pro každý soubor provede jeho zpracování - parse a vloření do vydaje
            3. uloží řádky do self.dictinary_list
        """
        dir_source = os.path.join(root_dir_trans_hist, dir_source)
        self.accName = acc_name
        flist = find_files(dir_source, file_mask)
        for fnameX in flist:
            print(self.__class__.__name__, fnameX)
            self.import_one_file(fnameX)
