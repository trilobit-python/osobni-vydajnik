import csv

import pandas

from .base_reader import xReader


class Raiffeisen_sporici_ucet(xReader):
    def read(self, root_dir_trans_hist, acc_name='Raiffeisen spořící účet', dir_source=r'raiffeisenbank\new_fmt_2018',
             file_mask='Pohyby_0646562010_*.csv'):

        super().read(root_dir_trans_hist, acc_name, dir_source, file_mask)

    @staticmethod
    def converter2(x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d.%m.%Y')

    def str_float(self, value):
        if isinstance(value, float):
            return value
        return float(value.replace(',', '.').replace(' ', ''))

    def import_one_file(self, full_file_name):
        """
        rozparsuje soubor a ulož do DB
        data sample: Pohyby_0646562010_201809271051.csv
        Datum provedení;Datum zaúčtování;Číslo účtu;Název účtu;Kategorie transakce;Číslo protiúčtu;Název protiúčtu
            ;Typ transakce;Zpráva;Poznámka;VS;KS;SS;Zaúčtovaná částka;Měna účtu;Původní částka a měna
            ;Původní částka a měna;Poplatek;Id transakce
        "31.08.2018";"31.08.2018 23:59";"646562010/5500";"Ing. David Němec";"Daň";"";"";"Daň z úroků"
            ;"Srážková daň";" ";"";"1148";"";"-57,33";"CZK";"";"";"";3303342709
        """

        # rozparsuje soubor a vloží data do výstupního DataFrame
        rows = pandas.read_csv(full_file_name, delimiter=';', encoding='cp1250', decimal=",",
                               converters={'Datum provedení': self.converter2},
                               keep_default_na=False, quoting=csv.QUOTE_ALL
                               )

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

            # values             Deposit /  Withdrawal
            if xTRANSAMOUNT > float(0):
                xTRANSCODE = 'Deposit'
            else:
                xTRANSAMOUNT = abs(xTRANSAMOUNT)
                xTRANSCODE = 'Withdrawal'
            #
            sPayee = row['Typ transakce']

            self.add_row(transcode=xTRANSCODE, transamount=xTRANSAMOUNT,
                         transactionnumber=xTRANSACTIONNUMBER,
                         note=xNOTES, date=xTRANSDATE, payee=sPayee)


class Raiffeisen_bezny_ucet(Raiffeisen_sporici_ucet):
    """ funkčnost implementována v rodič. třídě """

    def read(self, root_dir_trans_hist, acc_name='Raiffeisen běžný účet', dir_source=r'raiffeisenbank\new_fmt_2018',
             file_mask='Pohyby_0646562002_*.csv'):
        super().read(root_dir_trans_hist, acc_name, dir_source, file_mask)


class Raiffeisen_cards(xReader):
    def read(self, root_dir_trans_hist, acc_name='Raiffeisen_mala_i_velka_karta',
             dir_source=r'raiffeisenbank\new_fmt_2018',
             file_mask='Pohyby_531533XXXXXX*_*.csv'):

        super().read(root_dir_trans_hist, acc_name, dir_source, file_mask)

    @staticmethod
    def converter2(x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d.%m.%Y')

    def import_one_file(self, full_file_name):
        """
        rozparsuje soubor a ulož do DB
            nový formát od 9/2019 - obchodník a místo na konci řádku
        data sample: Pohyby_531533XXXXXX1199_201804111355.csv
        Číslo kreditní karty;Držitel karty;Datum transakce;Datum zúčtování;Typ transakce;Původní částka;Původní měna
            ;Zaúčtovaná částka;Měna zaúčtování;Převodní kurs;Popis/Místo transakce;Vlastní poznámka
            ;Název obchodníka;Město
        "531533XXXXXX0828";"David Němec";"19.06.2019";"20.06.2019";"Platba u obchodníka";"";"";"-1 090,00";"CZK";""
            ;"ORTOPEDICA S. R. O.";"";"";""
        rozparsuje soubor a vloží data do výstupního DataFrame
        """
        x_usecols = ['Číslo kreditní karty', 'Držitel karty', 'Datum transakce', 'Datum zúčtování',
                     'Typ transakce', 'Původní částka', 'Původní měna', 'Zaúčtovaná částka',
                     'Měna zaúčtování', 'Převodní kurs', 'Popis/Místo transakce', 'Vlastní poznámka',
                     'Název obchodníka', 'Město']
        rows = pandas.read_csv(full_file_name, delimiter=';', encoding='cp1250', usecols=x_usecols, decimal=",",
                               converters={'Datum transakce': self.converter2},
                               keep_default_na=False, quoting=csv.QUOTE_ALL
                               )

        for i, row in rows.iterrows():
            xTRANSDATE = row['Datum transakce'].strftime('%Y-%m-%d')  # 2014 - 10 - 21
            xNOTES = row['Popis/Místo transakce']

            xTRANSAMOUNT = self.str_float(row['Zaúčtovaná částka'])
            xstr = row['Původní částka'].strip()
            if xstr != '':
                xNOTES = ' '.join([xNOTES, str(row['Původní částka']), row['Původní měna'], row['Převodní kurs']])

            xTRANSACTIONNUMBER = row['Číslo kreditní karty'][-4:]

            if xNOTES == 'CARPISA METROPOLE ZLIC':
                xNOTES = xNOTES

            # values             Deposit /  Withdrawal
            if xTRANSAMOUNT > float(0):
                xTRANSCODE = 'Deposit'
            else:
                xTRANSAMOUNT = abs(xTRANSAMOUNT)
                xTRANSCODE = 'Withdrawal'
            sPayee = row['Typ transakce']

            self.add_row(transcode=xTRANSCODE, transamount=xTRANSAMOUNT,
                         transactionnumber=xTRANSACTIONNUMBER,
                         note=xNOTES, date=xTRANSDATE, payee=sPayee)
