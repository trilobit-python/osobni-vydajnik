import csv
import re
from io import StringIO

import pandas

from src.readers.base_reader import xReader


class mBank_bezny_ucet(xReader):
    @staticmethod
    def converter2(x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d-%m-%Y')

    def str_float(self, value):
        if isinstance(value, float):
            return value
        return float(value.replace(',', '.').replace(' ', ''))

    def import_one_file(self, full_file_name):
        # rozparsuje soubor a ulož do DB
        # data sample: 00593065_180301_180518.csv
        #
        # ;;;;;;#Počáteční zůstatek:;0,00 CZK;
        #
        # #Datum uskutečnění transakce;#Datum zaúčtování transakce;#Popis transakce;#Zpráva pro příjemce;#Plátce/Příjemce;#Číslo účtu plátce/příjemce;#KS;#VS;#SS;#Částka transakce;#Účetní zůstatek po transakci;
        # 07-02-2008;07-02-2008;ZŘÍZENÍ ÚČTU;"OTW. RACHUNKU";"  ";'';;;;0,00;0,00;
        # ...
        # 16-04-2018;16-04-2018;VÝBĚR Z BANKOMATU;"CS, ELISKY PREMYSLO/PRAHA-ZBRA                                        DATUM PROVEDENÍ TRANSAKCE: 2018-04-14";"  ";'';;;;-5 000,00;20 419,20;
        # ;;;;;;#Konečný zůstatek:;20 419,20 CZK;

        inp_lines = []
        in_read_section = False
        with open(full_file_name, encoding='windows-1250') as f:
            for line in f:
                line = line.strip()
                # odstraneni stredniku na konci radku je-li tam
                if line.endswith(';'):
                    line = line[0:len(line) - 1]
                if line == '':
                    in_read_section = False
                if line.startswith('#Datum '):
                    in_read_section = True
                if in_read_section:
                    # radek s hodnotami
                    inp_lines.append(line)
        a_string = "\n".join(inp_lines)

        # rozparsuje string a vloží data do výstupního DataFrame
        rows = pandas.read_csv(StringIO(a_string), delimiter=';', decimal=",",
                               converters={'#Datum uskutečnění transakce': self.converter2,
                                           '#Datum zaúčtování transakce': self.converter2},
                               keep_default_na=False, quoting=csv.QUOTE_ALL
                               )
        #
        for i, row in rows.iterrows():
            xTRANSDATE = row['#Datum uskutečnění transakce'].strftime('%Y-%m-%d')  # 2014 - 10 - 21
            xTRANSAMOUNT = self.str_float(row['#Částka transakce'])
            xStrings = [row['#Popis transakce'], row['#Zpráva pro příjemce'],
                        row['#Plátce/Příjemce'], row['#Číslo účtu plátce/příjemce'],
                        row['#KS'], row['#VS'], row['#SS']]
            xStrings = filter(lambda name: name.strip(), xStrings)
            xStrings = filter(lambda name: name != "\'\'", xStrings)
            xNOTES = ':'.join(filter(None, xStrings))
            # remove duplicate spaces
            xNOTES = " ".join(re.split("\s+", xNOTES, flags=re.UNICODE))

            xTRANSACTIONNUMBER = 'Stav:' + row['#Účetní zůstatek po transakci']

            # values             Deposit /  Withdrawal
            if xTRANSAMOUNT > float(0):
                xTRANSCODE = 'Deposit'
            else:
                xTRANSAMOUNT = abs(xTRANSAMOUNT)
                xTRANSCODE = 'Withdrawal'

            sPayee = row['#Plátce/Příjemce']

            self.add_row(transcode=xTRANSCODE, transamount=xTRANSAMOUNT,
                         transactionnumber=xTRANSACTIONNUMBER,
                         note=xNOTES, date=xTRANSDATE, payee=sPayee)

    def read(self, root_dir_trans_hist, acc_name='běžný účet mBank', dir_source='mbank',
             file_mask='00593065_*.csv'):

        super().read(root_dir_trans_hist, acc_name, dir_source, file_mask)


class mBank_podnikani_ucet(mBank_bezny_ucet):
    # -------------  funkčnost implementována v rodič. třídě

    def read(self, root_dir_trans_hist, acc_name='podnikatelský účet mBank', dir_source='mbank_zivnost',
             file_mask='mKonto_Business_15069717_*.csv'):
        super().read(root_dir_trans_hist, acc_name, dir_source, file_mask)
