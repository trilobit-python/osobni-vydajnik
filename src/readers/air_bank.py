import pandas

from src.readers.base_reader import xReader
from src.sqlite.sqlalchemy_declarative import CHECKINGACCOUNTV1


class airBankReader(xReader):
    def __init__(self, session, root_dir_trans_hist):
        xReader.__init__(self, session, 'běžný účet u Air bank', root_dir_trans_hist, 'air', '*.csv')

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