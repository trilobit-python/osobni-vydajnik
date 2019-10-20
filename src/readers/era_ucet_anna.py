import csv
import re
from io import StringIO

import pandas

from src.readers.base_reader import xReader
from src.sqlite.sqlalchemy_declarative import CHECKINGACCOUNTV1


class AnnaUcetEra(xReader):
    def __init__(self, session, root_dir_trans_hist):
        xReader.__init__(self, session, 'Anna účet Era', root_dir_trans_hist, r'AnnaUcetEra',
                         r'pohyby-na uctu 277150116_0300-*.csv')

    def converter2(self, x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d.%m.%Y')

    def import_one_file(self, full_file_name):
        # rozparsuje soubor a ulož do DB
        # Pohyby na účtu na účtu 277150116/0300 ze dne 19.02.2018 20:45:56;;;;;;;;;;;;;
        # ;;;;;;;;;;;;;
        # číslo účtu;datum zaúčtování;částka;měna;zůstatek;číslo účtu protiúčtu;kód banky protiúčtu;název účtu protiúčtu;konstantní symbol;variabilní symbol;specifický symbol;označení operace;ID transakce;poznámka
        # 277150116/0300;19.02.2018;-123,7;CZK;5753,78;;;;1178;205000049;6114181856;Transakce platební kartou;6924891286;Částka: 123,7 CZK 17.02.2018, Místo: ALBERT 0624, PRAHA 5
        # 277150116/0300;19.02.2018;-150;CZK;5877,48;;;;1178;205000048;6114181856;Transakce platební kartou;6924626436;Částka: 150 CZK 16.02.2018, Místo: TIGER, PRAHA
        # :rtype: object

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
        x_strings = ['ID transakce']
        rows['ord_num_in_grp'] = rows.groupby(x_strings).cumcount() + 1
        # #
        for i, row in rows.iterrows():
            xTRANSDATE = row['datum zaúčtování'].strftime('%Y-%m-%d')  # 2014 - 10 - 21
            xTRANSAMOUNT = self.str_float(row['částka'])
            xNOTES = row['poznámka']
            # remove duplicate spaces
            xNOTES = " ".join(re.split("\s+", xNOTES, flags=re.UNICODE))
            xTRANSACTIONNUMBER = row['ID transakce']
            ord_num_in_grp = row['ord_num_in_grp']
            #
            # values             Deposit /  Withdrawal
            if xTRANSAMOUNT > float(0):
                xTRANSCODE = 'Deposit'
            else:
                xTRANSAMOUNT = abs(xTRANSAMOUNT)
                xTRANSCODE = 'Withdrawal'
            #
            ret = self.session.query(CHECKINGACCOUNTV1.TRANSID).filter(
                CHECKINGACCOUNTV1.ACCOUNTID == self.accID, CHECKINGACCOUNTV1.TRANSDATE == xTRANSDATE,
                CHECKINGACCOUNTV1.TRANSAMOUNT == xTRANSAMOUNT,
                CHECKINGACCOUNTV1.TRANSACTIONNUMBER == xTRANSACTIONNUMBER).count()

            self.merge_to_DB(ord_num_in_grp, ret,
                             xTRANSCODE=xTRANSCODE, xTRANSAMOUNT=xTRANSAMOUNT,
                             xTRANSACTIONNUMBER=xTRANSACTIONNUMBER,
                             xNOTES=xNOTES, xTRANSDATE=xTRANSDATE)