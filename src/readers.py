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
        # rozparsuje soubor a ulo� transakce do vydaje
        super()

    def read(self):
        # 1. najde v�echny soubory v adres���ch
        # 2. pro ka�d� soubor provede jeho zpracov�n� - parse a vlo�en� do vydaje
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
            # OK existuje ji� pr�v� jeden v DB
            pass
        elif n_exists >= ord_num_in_grp:
            pass
        else:
            # print('Divny stav existuje vice nez 1')
            sKey = xTRANSACTIONNUMBER
            raise Exception(
                'Many records exists[%i] ord_num_in_grp[%i] in DB for key:%s '.format(n_exists, ord_num_in_grp, sKey))
            # kontrola pokud nen� jednozna�n� ��slo tranaskace (nap�. kreditn� karty)
            # kontrola dle     datum, castka, ucet, id transakce


class airBankReader(xReader):
    def __init__(self, session):
        xReader.__init__(self, session, 'air', 'b�n� ��et u Air bank', r'..\TransHist\air', '*.csv')

    def converter2(self, x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d/%m/%Y')

    def import_one_file(self, full_file_name):
        # rozparsuje soubor a ulo� do DB
        # data sample: airbank_1330098017_2018-05-02_13-29.csv
        #  "Datum proveden�";"Sm�r �hrady";"Typ �hrady";"Skupina plateb";"M�na ��tu";"��stka v m�n� ��tu";"Poplatek v m�n� ��tu";"P�vodn� m�na �hrady";"P�vodn� ��stka �hrady";"N�zev protistrany";"��slo ��tu protistrany";"N�zev ��tu protistrany";"Variabiln� symbol";"Konstantn� symbol";"Specifick� symbol";"Zdrojov� ob�lka";"C�lov� ob�lka";"Pozn�mka pro mne";"Zpr�va pro p��jemce";"Pozn�mka k �hrad�";"N�zev karty";"��slo karty";"Dr�itel karty";"�hrada mobilem";"Obchodn� m�sto";"Sm�nn� kurz";"Odes�latel poslal";"Poplatky jin�ch bank";"Datum a �as zad�n�";"Datum splatnosti";"Datum schv�len�";"Datum za��tov�n�";"Referen�n� ��slo";"Zp�sob zad�n�";"Zadal";"Za��tov�no";"Pojmenov�n� p��kazu";"N�zev, adresa a st�t protistrany";"N�zev, adresa a st�t banky protistrany";"Typ poplatku";"��el �hrady";"Zvl�tn� pokyny k �hrad�";"Souvisej�c� �hrady";"Dal�� identifikace �hrady"
        #  "06/06/2018";"Odchoz�";"Odchoz� SEPA �hrada";"Prispevek Nagyapa";"CZK";"-1648,84";"-25,00";"EUR";"-63,00";"Katka ucet";"SK6811000000002618111633/TATRSKBXXXX";"Katka ucet";;;;;;;"prispevek pece o seniory 2018/05   ";;;;;;"";"26,17";"";"";"06/06/2018 10:12:30";"06/06/2018";;"06/06/2018";"22247875732";"Internetov� bankovnictv�";"Ing. N�mec David";"";;"Katka ucet Zahradnicka 37                     811 07 Bratislava Slovensk� republika";"TATRA BANKA A.S. HODZOVO NAMESTIE 3 811 06 BRATISLAVA Slovensk� republika";"SHA";"";;;
        #  "11/05/2018";"Odchoz�";"Odchoz� SEPA �hrada";"Prispevek Nagyapa";"CZK";"-1722,47";"-25,00";"EUR";"-66,00";"Katka ucet";"SK6811000000002618111633/TATRSKBXXXX";"Katka ucet";;;;;;;"prispevek pece o seniory 2018/04   ";;;;;;"";"26,10";"";"";"11/05/2018 08:43:44";"11/05/2018";;"11/05/2018";"21804229852";"Internetov� bankovnictv�";"Ing. N�mec David";"";"KATKA ucet";"Katka ucet Zahradnicka 37                     811 07 Bratislava Slovensk� republika";"TATRA BANKA A.S. HODZOVO NAMESTIE 3 811 06 BRATISLAVA Slovensk� republika";"SHA";"";;;

        # rozparsuje soubor a vlo�� data do v�stupn�ho DataFrame
        x_usecols = ['Datum proveden�', '��stka v m�n� ��tu', 'Poplatek v m�n� ��tu', '��slo ��tu protistrany',
                     'N�zev ��tu protistrany', 'Zpr�va pro p��jemce', 'Pozn�mka k �hrad�', 'Referen�n� ��slo']
        rows = pandas.read_csv(full_file_name, delimiter=';', encoding='cp1250', usecols=x_usecols, decimal=",",
                               converters={'Datum proveden�': self.converter2}, keep_default_na=False)
        rows['ord_num_in_grp'] = rows.groupby(['Datum proveden�', '��stka v m�n� ��tu']).cumcount() + 1

        for i, row in rows.iterrows():
            # print(i, row)
            xTRANSDATE = row['Datum proveden�'].strftime('%Y-%m-%d')
            # 2014 - 10 - 21
            xTRANSAMOUNT = row['��stka v m�n� ��tu']
            xPoplatek = row['Poplatek v m�n� ��tu']
            if xPoplatek != '':
                nPoplatek = float(xPoplatek.replace(',', '.'))
                xTRANSAMOUNT = xTRANSAMOUNT + nPoplatek
            xTRANSACTIONNUMBER = row['Referen�n� ��slo']
            ord_num_in_grp = row['ord_num_in_grp']
            xNOTES = row['Pozn�mka k �hrad�'].strip()
            if xNOTES == '':
                xNOTES = row['Zpr�va pro p��jemce'].strip()
            if xNOTES == '':
                xNOTES = row['N�zev ��tu protistrany'].strip()
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
        # rozparsuje soubor a ulo� do DB
        # nov� form�t od 9/2019 - obchodn�k a m�sto na konci ��dku
        # data sample: Pohyby_531533XXXXXX1199_201804111355.csv
        # ��slo kreditn� karty;Dr�itel karty;Datum transakce;Datum z��tov�n�;Typ transakce;P�vodn� ��stka;P�vodn� m�na;Za��tovan� ��stka;M�na za��tov�n�;P�evodn� kurs;Popis/M�sto transakce;Vlastn� pozn�mka;N�zev obchodn�ka;M�sto
        # "531533XXXXXX0828";"David N�mec";"19.06.2019";"20.06.2019";"Platba u obchodn�ka";"";"";"-1 090,00";"CZK";"";"ORTOPEDICA S. R. O.";"";"";""
        # "531533XXXXXX0828";"David N�mec";"18.06.2019";"19.06.2019";"Platba u obchodn�ka";"";"";"-135,00";"CZK";"";"RANGOLI";"";"Rangoli";"Praha-Sm�chov"
        # rozparsuje soubor a vlo�� data do v�stupn�ho DataFrame
        x_usecols = ['��slo kreditn� karty', 'Dr�itel karty', 'Datum transakce', 'Datum z��tov�n�',
                     'Typ transakce', 'P�vodn� ��stka', 'P�vodn� m�na', 'Za��tovan� ��stka',
                     'M�na za��tov�n�', 'P�evodn� kurs', 'Popis/M�sto transakce', 'Vlastn� pozn�mka',
                     'N�zev obchodn�ka', 'M�sto']
        rows = pandas.read_csv(full_file_name, delimiter=';', encoding='cp1250', usecols=x_usecols, decimal=",",
                               converters={'Datum transakce': self.converter2},
                               keep_default_na=False, quoting=csv.QUOTE_ALL
                               )
        rows['ord_num_in_grp'] = rows.groupby(['Datum transakce', 'P�vodn� ��stka']).cumcount() + 1

        for i, row in rows.iterrows():
            xTRANSDATE = row['Datum transakce'].strftime('%Y-%m-%d')  # 2014 - 10 - 21
            xNOTES = row['Popis/M�sto transakce']

            xTRANSAMOUNT = self.str_float(row['Za��tovan� ��stka'])
            xstr = row['P�vodn� ��stka'].strip()
            if xstr != '':
                xNOTES = ' '.join([xNOTES, str(row['P�vodn� ��stka']), row['P�vodn� m�na'], row['P�evodn� kurs']])

            xTRANSACTIONNUMBER = row['��slo kreditn� karty'][-4:]
            ord_num_in_grp = row['ord_num_in_grp']

            # values             Deposit /  Withdrawal
            if xTRANSAMOUNT > float(0):
                xTRANSCODE = 'Deposit'
            else:
                xTRANSAMOUNT = abs(xTRANSAMOUNT)
                xTRANSCODE = 'Withdrawal'
            #
            # ret = self.session.query(CHECKINGACCOUNTV1.ACCOUNTID).filter(CHECKINGACCOUNTV1.ACCOUNTID == self.accID, CHECKINGACCOUNTV1.TRANSCODE ==  xTRANSCODE).scalar()
            str_like_notes = ''.join(['%', row['Popis/M�sto transakce'], '%'])
            ret = self.session.query(CHECKINGACCOUNTV1.TRANSID).filter(
                CHECKINGACCOUNTV1.ACCOUNTID == self.accID, CHECKINGACCOUNTV1.TRANSDATE == xTRANSDATE,
                CHECKINGACCOUNTV1.TRANSCODE == xTRANSCODE, CHECKINGACCOUNTV1.TRANSAMOUNT == xTRANSAMOUNT,
                CHECKINGACCOUNTV1.NOTES.like(str_like_notes)).count()

            self.merge_to_DB(ord_num_in_grp, ret,
                             xTRANSCODE=xTRANSCODE, xTRANSAMOUNT=xTRANSAMOUNT, xTRANSACTIONNUMBER=xTRANSACTIONNUMBER,
                             xNOTES=xNOTES, xTRANSDATE=xTRANSDATE)


class Raiffeisen_sporici_ucet(xReader):
    def __init__(self, session):
        xReader.__init__(self, session, '', 'Raiffeisen spo��c� ��et',
                         r'..\TransHist\raiffeisenbank\new_fmt_2018', 'Pohyby_0646562010_*.csv')

    def converter2(self, x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d.%m.%Y')

    def str_float(self, value):
        if isinstance(value, float):
            return value
        return float(value.replace(',', '.').replace(' ', ''))

    def import_one_file(self, full_file_name):
        # rozparsuje soubor a ulo� do DB
        # data sample: Pohyby_0646562010_201809271051.csv
        # Datum proveden�;Datum za��tov�n�;��slo ��tu;N�zev ��tu;Kategorie transakce;��slo proti��tu;N�zev proti��tu;Typ transakce;Zpr�va;Pozn�mka;VS;KS;SS;Za��tovan� ��stka;M�na ��tu;P�vodn� ��stka a m�na;P�vodn� ��stka a m�na;Poplatek;Id transakce
        # "31.08.2018";"31.08.2018 23:59";"646562010/5500";"Ing. David N�mec";"Da�";"";"";"Da� z �rok�";"Sr�kov� da�";" ";"";"1148";"";"-57,33";"CZK";"";"";"";3303342709
        # "10.05.2018";"10.05.2018 08:58";"646562010/5500";"Ing. David N�mec";"Platba";"670100-2215069717/6210";"DAVID NEMEC";"P��choz� platba";"P�EVOD PROST�EDK� - SPO�EN� V RB";" ";"";"";"";"5 000,00";"CZK";"";"";"";3215029129

        # rozparsuje soubor a vlo�� data do v�stupn�ho DataFrame
        rows = pandas.read_csv(full_file_name, delimiter=';', encoding='cp1250', decimal=",",
                               converters={'Datum proveden�': self.converter2},
                               keep_default_na=False, quoting=csv.QUOTE_ALL
                               )
        rows['ord_num_in_grp'] = rows.groupby('Id transakce').cumcount() + 1

        for i, row in rows.iterrows():
            xTRANSDATE = row['Datum proveden�'].strftime('%Y-%m-%d')  # 2014 - 10 - 21
            xTRANSAMOUNT = self.str_float(row['Za��tovan� ��stka'])
            xNOTES = row['Zpr�va']
            xstr = row['P�vodn� ��stka a m�na'].strip()
            if xstr != '':
                xTRANSAMOUNT = self.str_float(xstr)
                xNOTES = ' '.join([xNOTES, str(row['P�vodn� ��stka a m�na'])])

            if xNOTES == '':
                xNOTES = ' '.join([xNOTES, row['��slo proti��tu'], row['N�zev proti��tu'], row['Typ transakce']])

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
        xReader.__init__(self, session, '', 'Raiffeisen b�n� ��et',
                         r'..\TransHist\raiffeisenbank\new_fmt_2018', 'Pohyby_0646562002_*.csv')

    # -------------  funk�nost implementov�na v rodi�. t��d�


class mBank_bezny_ucet(xReader):
    def __init__(self, session):
        xReader.__init__(self, session, '', 'b�n� ��et mBank',
                         r'..\TransHist\mbank', 'mKonto_s_povolenym_precerpanim_00593065_*.csv')

    def converter2(self, x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d-%m-%Y')

    def str_float(self, value):
        if isinstance(value, float):
            return value
        return float(value.replace(',', '.').replace(' ', ''))

    def import_one_file(self, full_file_name):
        # rozparsuje soubor a ulo� do DB
        # data sample: mKonto_s_povolenym_precerpanim_00593065_180301_180518.csv
        #
        # ;;;;;;#Po��te�n� z�statek:;0,00 CZK;
        #
        # #Datum uskute�n�n� transakce;#Datum za��tov�n� transakce;#Popis transakce;#Zpr�va pro p��jemce;#Pl�tce/P��jemce;#��slo ��tu pl�tce/p��jemce;#KS;#VS;#SS;#��stka transakce;#��etn� z�statek po transakci;
        # 07-02-2008;07-02-2008;Z��ZEN� ��TU;"OTW. RACHUNKU";"  ";'';;;;0,00;0,00;
        # ...
        # 16-04-2018;16-04-2018;V�B�R Z BANKOMATU;"CS, ELISKY PREMYSLO/PRAHA-ZBRA                                        DATUM PROVEDEN� TRANSAKCE: 2018-04-14";"  ";'';;;;-5 000,00;20 419,20;
        # ;;;;;;#Kone�n� z�statek:;20 419,20 CZK;

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

        # rozparsuje string a vlo�� data do v�stupn�ho DataFrame
        rows = pandas.read_csv(StringIO(a_string), delimiter=';', decimal=",",
                               converters={'#Datum uskute�n�n� transakce': self.converter2,
                                           '#Datum za��tov�n� transakce': self.converter2},
                               keep_default_na=False, quoting=csv.QUOTE_ALL
                               )
        x_strings = ['#Datum uskute�n�n� transakce', '#��stka transakce', '#Popis transakce']
        rows['ord_num_in_grp'] = rows.groupby(x_strings).cumcount() + 1
        #
        for i, row in rows.iterrows():
            xTRANSDATE = row['#Datum uskute�n�n� transakce'].strftime('%Y-%m-%d')  # 2014 - 10 - 21
            xTRANSAMOUNT = self.str_float(row['#��stka transakce'])
            xStrings = [row['#Popis transakce'], row['#Zpr�va pro p��jemce'],
                        row['#Pl�tce/P��jemce'], row['#��slo ��tu pl�tce/p��jemce'],
                        row['#KS'], row['#VS'], row['#SS']]
            xStrings = filter(lambda name: name.strip(), xStrings)
            xStrings = filter(lambda name: name != "\'\'", xStrings)
            xNOTES = ':'.join(filter(None, xStrings))
            # remove duplicate spaces
            xNOTES = " ".join(re.split("\s+", xNOTES, flags=re.UNICODE))

            xTRANSACTIONNUMBER = 'Stav:' + row['#��etn� z�statek po transakci']
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
        xReader.__init__(self, session, '', '�ivnost_mBank',
                         r'..\TransHist\mbank', 'mKonto_Business_15069717_*.csv')

    # -------------  funk�nost implementov�na v rodi�. t��d�


class AnnaUcetEra(xReader):
    def __init__(self, session):
        xReader.__init__(self, session, 'air', 'Anna ��et Era', r'..\TransHist\AnnaUcetEra',
                         'pohyby-na uctu 277150116_0300-*.csv')

    def converter2(self, x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d.%m.%Y')

    def import_one_file(self, full_file_name):
        # rozparsuje soubor a ulo� do DB
        # Pohyby na ��tu na ��tu 277150116/0300 ze dne 19.02.2018 20:45:56;;;;;;;;;;;;;
        # ;;;;;;;;;;;;;
        # ��slo ��tu;datum za��tov�n�;��stka;m�na;z�statek;��slo ��tu proti��tu;k�d banky proti��tu;n�zev ��tu proti��tu;konstantn� symbol;variabiln� symbol;specifick� symbol;ozna�en� operace;ID transakce;pozn�mka
        # 277150116/0300;19.02.2018;-123,7;CZK;5753,78;;;;1178;205000049;6114181856;Transakce platebn� kartou;6924891286;��stka: 123,7 CZK 17.02.2018, M�sto: ALBERT 0624, PRAHA 5
        # 277150116/0300;19.02.2018;-150;CZK;5877,48;;;;1178;205000048;6114181856;Transakce platebn� kartou;6924626436;��stka: 150 CZK 16.02.2018, M�sto: TIGER, PRAHA
        # :rtype: object

        inp_lines = []
        with open(full_file_name, encoding='windows-1250') as f:
            for line in f:
                line = line.strip()
                if line:
                    # odstraneni stredniku na konci radku je-li tam
                    if line.endswith(';'):
                        line = line[0:len(line) - 1]
                    if line.startswith('Pohyby na ��tu na ��tu'):
                        pass
                    elif line.startswith(';;;;;;;;;'):
                        pass
                    elif line == "":
                        pass
                    else:
                        inp_lines.append(line)
        a_string = "\n".join(inp_lines)

        # rozparsuje string a vlo�� data do v�stupn�ho DataFrame
        rows = pandas.read_csv(StringIO(a_string), delimiter=';', decimal=",",
                               converters={'datum za��tov�n�': self.converter2},
                               keep_default_na=False, quoting=csv.QUOTE_NONE
                               )
        x_strings = ['ID transakce']
        rows['ord_num_in_grp'] = rows.groupby(x_strings).cumcount() + 1
        # #
        for i, row in rows.iterrows():
            xTRANSDATE = row['datum za��tov�n�'].strftime('%Y-%m-%d')  # 2014 - 10 - 21
            xTRANSAMOUNT = self.str_float(row['��stka'])
            xNOTES = row['pozn�mka']
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
