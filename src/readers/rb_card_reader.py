import csv

import pandas

from src.readers.base_reader import xReader
from src.sqlite.sqlalchemy_declarative import CHECKINGACCOUNTV1


class Raiffeisen_cards(xReader):
    def __init__(self, session, root_dir_trans_hist):
        xReader.__init__(self, session,
                         'Raiffeisen_mala_i_velka_karta',
                         root_dir_trans_hist, r'raiffeisenbank\new_fmt_2018', 'Pohyby_531533XXXXXX*_*.csv')

    def converter2(self, x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d.%m.%Y')

    def import_one_file(self, full_file_name):
        # rozparsuje soubor a ulož do DB
        # nový formát od 9/2019 - obchodník a místo na konci řádku
        # data sample: Pohyby_531533XXXXXX1199_201804111355.csv
        # Číslo kreditní karty;Držitel karty;Datum transakce;Datum zúčtování;Typ transakce;Původní částka;Původní měna;Zaúčtovaná částka;Měna zaúčtování;Převodní kurs;Popis/Místo transakce;Vlastní poznámka;Název obchodníka;Město
        # "531533XXXXXX0828";"David Němec";"19.06.2019";"20.06.2019";"Platba u obchodníka";"";"";"-1 090,00";"CZK";"";"ORTOPEDICA S. R. O.";"";"";""
        # "531533XXXXXX0828";"David Němec";"18.06.2019";"19.06.2019";"Platba u obchodníka";"";"";"-135,00";"CZK";"";"RANGOLI";"";"Rangoli";"Praha-Smíchov"
        # rozparsuje soubor a vloží data do výstupního DataFrame
        x_usecols = ['Číslo kreditní karty', 'Držitel karty', 'Datum transakce', 'Datum zúčtování',
                     'Typ transakce', 'Původní částka', 'Původní měna', 'Zaúčtovaná částka',
                     'Měna zaúčtování', 'Převodní kurs', 'Popis/Místo transakce', 'Vlastní poznámka',
                     'Název obchodníka', 'Město']
        rows = pandas.read_csv(full_file_name, delimiter=';', encoding='cp1250', usecols=x_usecols, decimal=",",
                               converters={'Datum transakce': self.converter2},
                               keep_default_na=False, quoting=csv.QUOTE_ALL
                               )
        rows['ord_num_in_grp'] = rows.groupby(
            ['Datum transakce', 'Zaúčtovaná částka', 'Původní částka', 'Popis/Místo transakce']).cumcount() + 1

        for i, row in rows.iterrows():
            xTRANSDATE = row['Datum transakce'].strftime('%Y-%m-%d')  # 2014 - 10 - 21
            xNOTES = row['Popis/Místo transakce']

            xTRANSAMOUNT = self.str_float(row['Zaúčtovaná částka'])
            xstr = row['Původní částka'].strip()
            if xstr != '':
                xNOTES = ' '.join([xNOTES, str(row['Původní částka']), row['Původní měna'], row['Převodní kurs']])

            xTRANSACTIONNUMBER = row['Číslo kreditní karty'][-4:]
            ord_num_in_grp = row['ord_num_in_grp']

            if xNOTES == 'CARPISA METROPOLE ZLIC':
                xNOTES = xNOTES

            # values             Deposit /  Withdrawal
            if xTRANSAMOUNT > float(0):
                xTRANSCODE = 'Deposit'
            else:
                xTRANSAMOUNT = abs(xTRANSAMOUNT)
                xTRANSCODE = 'Withdrawal'
            #
            # ret = self.session.query(CHECKINGACCOUNTV1.ACCOUNTID).filter(CHECKINGACCOUNTV1.ACCOUNTID == self.accID, CHECKINGACCOUNTV1.TRANSCODE ==  xTRANSCODE).scalar()
            str_like_notes = ''.join(['%', row['Popis/Místo transakce'], '%'])
            ret = self.session.query(CHECKINGACCOUNTV1.TRANSID).filter(
                CHECKINGACCOUNTV1.ACCOUNTID == self.accID, CHECKINGACCOUNTV1.TRANSDATE == xTRANSDATE,
                CHECKINGACCOUNTV1.TRANSCODE == xTRANSCODE, CHECKINGACCOUNTV1.TRANSAMOUNT == xTRANSAMOUNT,
                CHECKINGACCOUNTV1.NOTES.like(str_like_notes)).count()

            self.merge_to_DB(ord_num_in_grp, ret,
                             xTRANSCODE=xTRANSCODE, xTRANSAMOUNT=xTRANSAMOUNT, xTRANSACTIONNUMBER=xTRANSACTIONNUMBER,
                             xNOTES=xNOTES, xTRANSDATE=xTRANSDATE)