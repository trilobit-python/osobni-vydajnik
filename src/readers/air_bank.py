import pandas

from .base_reader import xReader


class AirBankReader(xReader):
    def read(self, root_dir_trans_hist, acc_name, dir_source, file_mask):
        return super().read(root_dir_trans_hist, acc_name, dir_source, file_mask)

    @staticmethod
    def converter2(x):
        # define format of datetime
        return pandas.to_datetime(x, format='%d/%m/%Y')

    def import_one_file(self, full_file_name):
        """
            rozparsuje soubor a pro každý řádek zavolá přidání do dat předka
            data sample: airbank_1330098017_2018-05-02_13-29.csv
             "Datum provedení";"Směr úhrady";"Typ úhrady";"Skupina plateb";"Měna účtu";"Částka v měně účtu"
               ;"Poplatek v měně účtu";"Původní měna úhrady";"Původní částka úhrady";"Název protistrany"
               ;"Číslo účtu protistrany";"Název účtu protistrany";"Variabilní symbol";"Konstantní symbol"
               ;"Specifický symbol";"Zdrojová obálka";"Cílová obálka";"Poznámka pro mne";"Zpráva pro příjemce"
               ;"Poznámka k úhradě";"Název karty";"Číslo karty";"Držitel karty";"Úhrada mobilem";"Obchodní místo"
               ;"Směnný kurz";"Odesílatel poslal";"Poplatky jiných bank";"Datum a čas zadání";"Datum splatnosti"
               ;"Datum schválení";"Datum zaúčtování";"Referenční číslo";"Způsob zadání";"Zadal";"Zaúčtováno"
               ;"Pojmenování příkazu";"Název, adresa a stát protistrany";"Název, adresa a stát banky protistrany"
               ;"Typ poplatku";"Účel úhrady";"Zvláštní pokyny k úhradě";"Související úhrady";"Další identifikace úhrady"
             "06/06/2018";"Odchozí";"Odchozí SEPA úhrada";"Prispevek Nagyapa";"CZK";"-1648,84";"-25,00";"EUR";"-63,00"
               ;"Katka ucet";"SK6811000000002618111633/TATRSKBXXXX";"Katka ucet";;;;;;
               ;"prispevek pece o seniory 2018/05   ";;;;;;"";"26,17";"";"";"06/06/2018 10:12:30";"06/06/2018";
               ;"06/06/2018";"22247875732";"Internetové bankovnictví";"Ing. Němec David";"";
               ;"Katka ucet Zahradnicka 37                     811 07 Bratislava Slovenská republika"
               ;"TATRA BANKA A.S. HODZOVO NAMESTIE 3 811 06 BRATISLAVA Slovenská republika";"SHA";"";;;
        """

        # rozparsuje soubor a vloží data do výstupního DataFram
        x_usecols = ['Datum provedení', 'Částka v měně účtu', 'Poplatek v měně účtu', 'Číslo účtu protistrany',
                     'Název účtu protistrany', 'Zpráva pro příjemce', 'Poznámka k úhradě', 'Referenční číslo',
                     'Typ úhrady']
        rows = pandas.read_csv(full_file_name, delimiter=';', encoding='cp1250', usecols=x_usecols, decimal=",",
                               converters={'Datum provedení': self.converter2}, keep_default_na=False)

        for i, row in rows.iterrows():
            x_transdate = row['Datum provedení'].strftime('%Y-%m-%d')
            x_transamount = row['Částka v měně účtu']
            x_poplatek = row['Poplatek v měně účtu']
            if x_poplatek != '':
                n_poplatek = float(x_poplatek.replace(',', '.'))
                x_transamount = x_transamount + n_poplatek
            x_transactionnumber = row['Referenční číslo']
            x_notes = row['Poznámka k úhradě'].strip()
            if x_notes == '':
                x_notes = row['Zpráva pro příjemce'].strip()
            if x_notes == '':
                x_notes = row['Název účtu protistrany'].strip()
            # values             Deposit /  Withdrawal
            if x_transamount > float(0):
                x_transcode = 'Deposit'
            else:
                x_transamount = abs(x_transamount)
                x_transcode = 'Withdrawal'

            payee = row['Typ úhrady']

            self.add_row(transcode=x_transcode, transamount=x_transamount,
                         transactionnumber=x_transactionnumber,
                         note=x_notes, date=x_transdate, payee=payee)


class AirBankBeznyUcet(AirBankReader):
    """ funkčnost implementována v rodič. třídě """

    def read(self, root_dir_trans_hist, acc_name='běžný účet u Air bank', dir_source='air',
             file_mask='airbank_1330098017_*.csv'):
        super().read(root_dir_trans_hist, acc_name, dir_source, file_mask)


class AirBankSporiciUcet(AirBankReader):
    """ funkčnost implementována v rodič. třídě """

    def read(self, root_dir_trans_hist, acc_name='AirBank spořící účet', dir_source='air',
             file_mask='airbank_1330098025_*.csv'):
        super().read(root_dir_trans_hist, acc_name, dir_source, file_mask)
