import csv

import pandas

from src.readers.base_reader import xReader
from src.sqlite.sqlalchemy_declarative import CHECKINGACCOUNTV1


class Raiffeisen_sporici_ucet(xReader):
    def __init__(self, session, root_dir_trans_hist):
        xReader.__init__(self, session, 'Raiffeisen spořící účet',
                         root_dir_trans_hist, r'raiffeisenbank\new_fmt_2018', 'Pohyby_0646562010_*.csv')

    def converter2(self, x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d.%m.%Y')

    def str_float(self, value):
        if isinstance(value, float):
            return value
        return float(value.replace(',', '.').replace(' ', ''))

    def import_one_file(self, full_file_name):
        # rozparsuje soubor a ulož do DB
        # data sample: Pohyby_0646562010_201809271051.csv
        # Datum provedení;Datum zaúčtování;Číslo účtu;Název účtu;Kategorie transakce;Číslo protiúčtu;Název protiúčtu;Typ transakce;Zpráva;Poznámka;VS;KS;SS;Zaúčtovaná částka;Měna účtu;Původní částka a měna;Původní částka a měna;Poplatek;Id transakce
        # "31.08.2018";"31.08.2018 23:59";"646562010/5500";"Ing. David Němec";"Daň";"";"";"Daň z úroků";"Srážková daň";" ";"";"1148";"";"-57,33";"CZK";"";"";"";3303342709
        # "10.05.2018";"10.05.2018 08:58";"646562010/5500";"Ing. David Němec";"Platba";"670100-2215069717/6210";"DAVID NEMEC";"Příchozí platba";"PŘEVOD PROSTŘEDKŮ - SPOŘENÍ V RB";" ";"";"";"";"5 000,00";"CZK";"";"";"";3215029129

        # rozparsuje soubor a vloží data do výstupního DataFrame
        rows = pandas.read_csv(full_file_name, delimiter=';', encoding='cp1250', decimal=",",
                               converters={'Datum provedení': self.converter2},
                               keep_default_na=False, quoting=csv.QUOTE_ALL
                               )
        rows['ord_num_in_grp'] = rows.groupby('Id transakce').cumcount() + 1

        for i, row in rows.iterrows():
            xTRANSDATE = row['Datum provedení'].strftime('%Y-%m-%d')  # 2014 - 10 - 21
            xTRANSAMOUNT = self.str_float(row['Zaúčtovaná částka'])
            xNOTES = row['Zpráva']
            xstr = row['Původní částka a měna'].strip()
            if xstr != '':
                xTRANSAMOUNT = self.str_float(xstr)
                xNOTES = ' '.join([xNOTES, str(row['Původní částka a měna'])])

            if xNOTES == '':
                xNOTES = ' '.join([xNOTES, row['Číslo protiúčtu'], row['Název protiúčtu'], row['Typ transakce']])

            xTRANSACTIONNUMBER = row['Id transakce']
            ord_num_in_grp = row['ord_num_in_grp']

            # values             Deposit /  Withdrawal
            if xTRANSAMOUNT > float(0):
                xTRANSCODE = 'Deposit'
            else:
                xTRANSAMOUNT = abs(xTRANSAMOUNT)
                xTRANSCODE = 'Withdrawal'
            #
            ret = self.session.query(CHECKINGACCOUNTV1.TRANSID).filter(CHECKINGACCOUNTV1.ACCOUNTID == self.accID,
                                                                       CHECKINGACCOUNTV1.TRANSACTIONNUMBER == xTRANSACTIONNUMBER).count()
            self.merge_to_DB(ord_num_in_grp, ret,
                             xTRANSCODE=xTRANSCODE, xTRANSAMOUNT=xTRANSAMOUNT, xTRANSACTIONNUMBER=xTRANSACTIONNUMBER,
                             xNOTES=xNOTES, xTRANSDATE=xTRANSDATE)