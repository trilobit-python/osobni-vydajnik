import csv
import re
from io import StringIO

import pandas

from .base_reader import xReader


class AnnaUcetEra(xReader):
    def read(self, root_dir_trans_hist, acc_name='Anna účet Era', dir_source='AnnaUcetEra',
             file_mask='pohyby-na uctu 277150116_0300-*.csv'):

        super().read(root_dir_trans_hist, acc_name, dir_source, file_mask)

    @staticmethod
    def converter2(x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d.%m.%Y')

    def import_one_file(self, full_file_name):
        """
        rozparsuje soubor a ulož do DB
        Pohyby na účtu na účtu 277150116/0300 ze dne 19.02.2018 20:45:56;;;;;;;;;;;;;
        ;;;;;;;;;;;;;
        Vzroek dat
        číslo účtu;datum zaúčtování;částka;měna;zůstatek;číslo účtu protiúčtu;kód banky protiúčtu
            ;název účtu protiúčtu;konstantní symbol;variabilní symbol;specifický symbol;označení operace;
            ID transakce;poznámka
        277150116/0300;19.02.2018;-123,7;CZK;5753,78;;;;1178;205000049;6114181856;Transakce platební kartou;6924891286;Částka: 123,7 CZK 17.02.2018, Místo: ALBERT 0624, PRAHA 5
        277150116/0300;19.02.2018;-150;CZK;5877,48;;;;1178;205000048;6114181856;Transakce platební kartou;6924626436;Částka: 150 CZK 16.02.2018, Místo: TIGER, PRAHA
        """
        inp_lines = []
        with open(full_file_name, encoding='windows-1250') as f:
            for line in f:
                line = line.strip()
                if line:
                    # odstraneni stredniku na konci radku je-li tam
                    if line.endswith(';'):
                        line = line[0:len(line) - 1]
                    if line.startswith('Pohyby na účtu na účtu'):
                        pass
                    elif line.startswith(';;;;;;;;;'):
                        pass
                    elif line == "":
                        pass
                    else:
                        inp_lines.append(line)
        a_string = "\n".join(inp_lines)

        # rozparsuje string a vloží data do výstupního DataFrame
        rows = pandas.read_csv(StringIO(a_string), delimiter=';', decimal=",",
                               converters={'datum zaúčtování': self.converter2},
                               keep_default_na=False, quoting=csv.QUOTE_NONE
                               )
        # #
        for i, row in rows.iterrows():
            xTRANSDATE = row['datum zaúčtování'].strftime('%Y-%m-%d')  # 2014 - 10 - 21
            xTRANSAMOUNT = self.str_float(row['částka'])
            xNOTES = row['poznámka']
            # remove duplicate spaces
            xNOTES = " ".join(re.split("\s+", xNOTES, flags=re.UNICODE))
            xTRANSACTIONNUMBER = row['ID transakce']
            #
            # values             Deposit /  Withdrawal
            if xTRANSAMOUNT > float(0):
                xTRANSCODE = 'Deposit'
            else:
                xTRANSAMOUNT = abs(xTRANSAMOUNT)
                xTRANSCODE = 'Withdrawal'
            #
            sPayee = row['označení operace']

            self.add_row(transcode=xTRANSCODE, transamount=xTRANSAMOUNT,
                         transactionnumber=xTRANSACTIONNUMBER,
                         note=xNOTES, date=xTRANSDATE, payee=sPayee)
