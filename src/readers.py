#!/usr/bin/env python
# -*- coding: windows-1250 -*-

import csv
import re
from io import StringIO

import pandas

from common_utils import find_files, getACCOUNTID, getPAYEEID
from sqlalchemy_declarative import CHECKINGACCOUNTV1


def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))
    return d


class xReader:
    def __init__(self, session, p_payeeName, p_accName, p_dirSource, p_fileMask):  # konstruktor
        self.payeeName = p_payeeName
        self.ccName = p_accName
        self.dirSource = p_dirSource
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
            PAYEEID=self.PAYEEID,
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


class airBankReader(xReader):
    def __init__(self, session):
        xReader.__init__(self, session, 'air', 'běžný účet u Air bank', r'..\TransHist\air', '*.csv')

    def converter2(self, x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d/%m/%Y')

    def import_one_file(self, full_file_name):
        # rozparsuje soubor a ulož do DB
        # data sample: airbank_1330098017_2018-05-02_13-29.csv
        #  "Datum provedení";"Směr úhrady";"Typ úhrady";"Skupina plateb";"Měna účtu";"Částka v měně účtu";"Poplatek v měně účtu";"Původní měna úhrady";"Původní částka úhrady";"Název protistrany";"Číslo účtu protistrany";"Název účtu protistrany";"Variabilní symbol";"Konstantní symbol";"Specifický symbol";"Zdrojová obálka";"Cílová obálka";"Poznámka pro mne";"Zpráva pro příjemce";"Poznámka k úhradě";"Název karty";"Číslo karty";"Držitel karty";"Úhrada mobilem";"Obchodní místo";"Směnný kurz";"Odesílatel poslal";"Poplatky jiných bank";"Datum a čas zadání";"Datum splatnosti";"Datum schválení";"Datum zaúčtování";"Referenční číslo";"Způsob zadání";"Zadal";"Zaúčtováno";"Pojmenování příkazu";"Název, adresa a stát protistrany";"Název, adresa a stát banky protistrany";"Typ poplatku";"Účel úhrady";"Zvláštní pokyny k úhradě";"Související úhrady";"Další identifikace úhrady"
        #  "06/06/2018";"Odchozí";"Odchozí SEPA úhrada";"Prispevek Nagyapa";"CZK";"-1648,84";"-25,00";"EUR";"-63,00";"Katka ucet";"SK6811000000002618111633/TATRSKBXXXX";"Katka ucet";;;;;;;"prispevek pece o seniory 2018/05   ";;;;;;"";"26,17";"";"";"06/06/2018 10:12:30";"06/06/2018";;"06/06/2018";"22247875732";"Internetové bankovnictví";"Ing. Němec David";"";;"Katka ucet Zahradnicka 37                     811 07 Bratislava Slovenská republika";"TATRA BANKA A.S. HODZOVO NAMESTIE 3 811 06 BRATISLAVA Slovenská republika";"SHA";"";;;
        #  "11/05/2018";"Odchozí";"Odchozí SEPA úhrada";"Prispevek Nagyapa";"CZK";"-1722,47";"-25,00";"EUR";"-66,00";"Katka ucet";"SK6811000000002618111633/TATRSKBXXXX";"Katka ucet";;;;;;;"prispevek pece o seniory 2018/04   ";;;;;;"";"26,10";"";"";"11/05/2018 08:43:44";"11/05/2018";;"11/05/2018";"21804229852";"Internetové bankovnictví";"Ing. Němec David";"";"KATKA ucet";"Katka ucet Zahradnicka 37                     811 07 Bratislava Slovenská republika";"TATRA BANKA A.S. HODZOVO NAMESTIE 3 811 06 BRATISLAVA Slovenská republika";"SHA";"";;;

        # rozparsuje soubor a vloží data do výstupního DataFrame
        x_usecols = ['Datum provedení', 'Částka v měně účtu', 'Poplatek v měně účtu', 'Číslo účtu protistrany',
                     'Název účtu protistrany', 'Zpráva pro příjemce', 'Poznámka k úhradě', 'Referenční číslo']
        rows = pandas.read_csv(full_file_name, delimiter=';', encoding='cp1250', usecols=x_usecols, decimal=",",
                               converters={'Datum provedení': self.converter2}, keep_default_na=False)
        rows['ord_num_in_grp'] = rows.groupby(['Datum provedení', 'Částka v měně účtu']).cumcount() + 1

        for i, row in rows.iterrows():
            # print(i, row)
            xTRANSDATE = row['Datum provedení'].strftime('%Y-%m-%d')
            # 2014 - 10 - 21
            xTRANSAMOUNT = row['Částka v měně účtu']
            xPoplatek = row['Poplatek v měně účtu']
            if xPoplatek != '':
                nPoplatek = float(xPoplatek.replace(',', '.'))
                xTRANSAMOUNT = xTRANSAMOUNT + nPoplatek
            xTRANSACTIONNUMBER = row['Referenční číslo']
            ord_num_in_grp = row['ord_num_in_grp']
            xNOTES = row['Poznámka k úhradě'].strip()
            if xNOTES == '':
                xNOTES = row['Zpráva pro příjemce'].strip()
            if xNOTES == '':
                xNOTES = row['Název účtu protistrany'].strip()
            # values             Deposit /  Withdrawal
            if xTRANSAMOUNT > float(0):
                xTRANSCODE = 'Deposit'
            else:
                xTRANSAMOUNT = abs(xTRANSAMOUNT)
                xTRANSCODE = 'Withdrawal'

            # ret = self.session.query(CHECKINGACCOUNTV1.ACCOUNTID).filter(CHECKINGACCOUNTV1.ACCOUNTID == self.accID, CHECKINGACCOUNTV1.TRANSCODE ==  xTRANSCODE).scalar()
            ret = self.session.query(CHECKINGACCOUNTV1.TRANSID).filter(CHECKINGACCOUNTV1.ACCOUNTID == self.accID,
                                                                       CHECKINGACCOUNTV1.TRANSDATE == xTRANSDATE,
                                                                       CHECKINGACCOUNTV1.TRANSAMOUNT == xTRANSAMOUNT).count()
            self.merge_to_DB(ord_num_in_grp, ret,
                             xTRANSCODE=xTRANSCODE, xTRANSAMOUNT=xTRANSAMOUNT, xTRANSACTIONNUMBER=xTRANSACTIONNUMBER,
                             xNOTES=xNOTES, xTRANSDATE=xTRANSDATE)


class Raiffeisen_cards(xReader):
    def __init__(self, session):
        xReader.__init__(self, session, '',
                         'Raiffeisen_mala_i_velka_karta',
                         # Pohyby_531533XXXXXX1719_201901131516.csv
                         # Pohyby_531533XXXXXX0828_201901131515.csv
                         r'..\TransHist\raiffeisenbank\new_fmt_2018', 'Pohyby_531533XXXXXX*_*.csv')

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
        rows['ord_num_in_grp'] = rows.groupby(['Datum transakce', 'Původní částka']).cumcount() + 1

        for i, row in rows.iterrows():
            xTRANSDATE = row['Datum transakce'].strftime('%Y-%m-%d')  # 2014 - 10 - 21
            xNOTES = row['Popis/Místo transakce']

            xTRANSAMOUNT = self.str_float(row['Zaúčtovaná částka'])
            xstr = row['Původní částka'].strip()
            if xstr != '':
                xNOTES = ' '.join([xNOTES, str(row['Původní částka']), row['Původní měna'], row['Převodní kurs']])

            xTRANSACTIONNUMBER = row['Číslo kreditní karty'][-4:]
            ord_num_in_grp = row['ord_num_in_grp']

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


class Raiffeisen_sporici_ucet(xReader):
    def __init__(self, session):
        xReader.__init__(self, session, '', 'Raiffeisen spořící účet',
                         r'..\TransHist\raiffeisenbank\new_fmt_2018', 'Pohyby_0646562010_*.csv')

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


class Raiffeisen_bezny_ucet(Raiffeisen_sporici_ucet):
    def __init__(self, session):
        xReader.__init__(self, session, '', 'Raiffeisen běžný účet',
                         r'..\TransHist\raiffeisenbank\new_fmt_2018', 'Pohyby_0646562002_*.csv')

    # -------------  funkčnost implementována v rodič. třídě


class mBank_bezny_ucet(xReader):
    def __init__(self, session):
        xReader.__init__(self, session, '', 'běžný účet mBank',
                         r'..\TransHist\mbank', 'mKonto_s_povolenym_precerpanim_00593065_*.csv')

    def converter2(self, x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d-%m-%Y')

    def str_float(self, value):
        if isinstance(value, float):
            return value
        return float(value.replace(',', '.').replace(' ', ''))

    def import_one_file(self, full_file_name):
        # rozparsuje soubor a ulož do DB
        # data sample: mKonto_s_povolenym_precerpanim_00593065_180301_180518.csv
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
        x_strings = ['#Datum uskutečnění transakce', '#Částka transakce', '#Popis transakce']
        rows['ord_num_in_grp'] = rows.groupby(x_strings).cumcount() + 1
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
            ord_num_in_grp = row['ord_num_in_grp']

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
                CHECKINGACCOUNTV1.NOTES.like(row['#Popis transakce'] + '%')).count()

            self.merge_to_DB(ord_num_in_grp, ret,
                             xTRANSCODE=xTRANSCODE, xTRANSAMOUNT=xTRANSAMOUNT,
                             xTRANSACTIONNUMBER=xTRANSACTIONNUMBER,
                             xNOTES=xNOTES, xTRANSDATE=xTRANSDATE)


class mBank_podnikani_ucet(mBank_bezny_ucet):
    def __init__(self, session):
        xReader.__init__(self, session, '', 'živnost_mBank',
                         r'..\TransHist\mbank', 'mKonto_Business_15069717_*.csv')

    # -------------  funkčnost implementována v rodič. třídě


class AnnaUcetEra(xReader):
    def __init__(self, session):
        xReader.__init__(self, session, 'air', 'Anna účet Era', r'..\TransHist\AnnaUcetEra',
                         'pohyby-na uctu 277150116_0300-*.csv')

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
