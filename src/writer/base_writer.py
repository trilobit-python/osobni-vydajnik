#!/usr/bin/env python
# -*- coding: windows-1250 -*-
from collections import Counter

import pandas as pd
from pandas import Series

from ..readers.base_reader import xReader
from ..utils.common import print_frame
from ..utils.sqlite_database import SqliteDatabase
from .category_setter import CategorySetter
from .konstanty import CATEGID_NEZNAMA

class Writer:
    """ Implementuje zápis do MMX databáze sqlite"""

    def __init__(self, p_db: SqliteDatabase):
        self.db = p_db
        # načtení neměněnných tabulek do paměti
        self.dfUcty = self.db.query('select * from ACCOUNTLIST_V1 order by 1')
        self.dfUcty.set_index('ACCOUNTID', inplace=True)
        self.dfKategorie = self.db.query('select * from CATEGORY_V1 order by 1')
        self.dfKategorie.set_index('CATEGID', inplace=True)
        self.dfPodKategorie = self.db.query('select * from SUBCATEGORY_V1 order by 1')
        self.dfPodKategorie.set_index('SUBCATEGID', inplace=True)

    # def __del__(self):
    #     del self
    #
    # def __enter__(self):
    #     try:
    #         self.conn = sqlite3.connect(self.db_file)
    #         print('OK sqlite3 connect')
    #     except sqlite3.Error:
    #         raise ValueError(f'Failed to connect to database! {sqlite3.Error}')
    #     return self
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     if self.conn:
    #         self.conn.rollback()
    #         self.conn.close()

    def set_categories(self, root_dir_trans_hist):
        setter = CategorySetter(root_dir_trans_hist, self.db, self.dfKategorie,
                                self.dfPodKategorie, self.dfUcty)
        setter.set_categories()

    def show_rule_candidates(self):
        sql_txt = '''
            SELECT NOTES, Pocet, SumCastka, MinDate, MaxDate
              from v_statistika_bez_kategorie
             where pocet > 1
             order by pocet desc
        '''
        result = self.db.query(sql_txt)
        print_frame(result, '\n* Kandidáti na pravidlo *', '   ')

    def zapis_do_db(self, reader: xReader):
        df_ucet_info = self.dfUcty[self.dfUcty.ACCOUNTNAME == reader.accName]
        if len(df_ucet_info.index):
            # zapis DataFrame z readeru do DB
            accountid = int(df_ucet_info.index[0])
            df_existujici_pohyby = self.db.query('select * from CHECKINGACCOUNT_V1 where ACCOUNTID = :id',
                                                 p_params={'id': accountid})
            df_existujici_pohyby.set_index('TRANSID', inplace=True)

            str_datum_posl_pohyb_na_ucte = '2000-01-01'
            if len(df_existujici_pohyby.index):
                str_datum_posl_pohyb_na_ucte = df_existujici_pohyby.TRANSDATE.max()

            df_csv_radky = reader.get_data_frame()

            # odstraň řádky před datem posledního importu
            df_csv_radky = df_csv_radky[df_csv_radky['Datum'] >= str_datum_posl_pohyb_na_ucte]

            # kopie prázdné struktury
            nove_vkladane_radky = pd.DataFrame(data=None, columns=df_existujici_pohyby.columns,
                                               index=None)
            nove_vkladane_radky.index.names = df_existujici_pohyby.index.names

            for index, row in df_csv_radky.iterrows():
                # najdi existující záznamy se stejnými hodnotami na stejném účtu
                dict_values = dict(
                    ACCOUNTID=accountid, TOACCOUNTID=-1, PAYEEID=1,
                    TRANSCODE=row['Operace'], TRANSAMOUNT=row['Částka'], STATUS=df_ucet_info.ACCOUNTNAME.values[0],
                    TRANSACTIONNUMBER=row['ID transakce'], NOTES=row['Poznámka'].strip(), TRANSDATE=row['Datum'],
                    FOLLOWUPID=-1, TOTRANSAMOUNT=0, TRANSID=None, CATEGID=CATEGID_NEZNAMA, SUBCATEGID=None, SUPERTYPE=None)

                df_stejne = df_existujici_pohyby[(df_existujici_pohyby["ACCOUNTID"] == accountid)
                                                 & (df_existujici_pohyby["TRANSDATE"] == dict_values['TRANSDATE'])
                                                 & (df_existujici_pohyby["TRANSAMOUNT"] == dict_values['TRANSAMOUNT'])
                                                 & ((df_existujici_pohyby["TRANSCODE"] == dict_values['TRANSCODE']) |
                                                    df_existujici_pohyby["TRANSCODE"].str.startswith('Transfer'))]
                #  pokud je více a existuje číslo transakce přidáme do filtru
                if len(df_stejne.index) > 1 & len(str(row['ID transakce'])) > 0:
                    df_stejne = df_stejne[
                        (df_existujici_pohyby["TRANSACTIONNUMBER"] == row['ID transakce'])]

                if len(df_stejne.index) > 1 & len(row['Poznámka']) > 0:
                    df_stejne = df_stejne[(df_existujici_pohyby["NOTES"].str.startswith(row['Poznámka']))]

                if len(df_stejne.index) == 0:  # nová hodnota pro vložení
                    print(f'Insert {str(dict_values)}')
                    nove_vkladane_radky = nove_vkladane_radky.append(dict_values, ignore_index=True)
                elif len(df_stejne.index) == 1:  # OK existuje již právě jeden v DB
                    pass
                else:
                    # vyjímka nákup v automatu 2x stejný den stejná položka , nebyly čísla transakcí tehdá...
                    if dict_values.get('ACCOUNTID', 0) == 11 \
                            and dict_values.get('NOTES', 0) == 'PLATBA KARTOU:OVI STORE /HELSINKI' \
                            and row.TRANSDATE == '2010-05-03':
                        #     vyjímka dva stejné pohyby v 1 den stejná částka i poznámka historii mBank nelze rozlišit
                        pass
                    else:
                        raise Exception(
                            f'Existuje {len(df_stejne.index)} záznamů v účtu:'
                            f'{accountid}-{df_ucet_info.ACCOUNTNAME.values[0]} pro zdrojový:{str(row)}')

            if len(nove_vkladane_radky.index):
                print(f'Celkem pro INSERT hodnot: {len(nove_vkladane_radky.index)}')
                nove_vkladane_radky.to_sql('CHECKINGACCOUNT_V1', self.db.connection(), if_exists='append', index=False)
                self.db.commit()

    def compute_super_type(self, p_transakce: Series):
        """Spočte Supertyp z pohybu a druhu účtu
                 složité rozhodování jak nastavit sloupec SUPERTYPE
            význam hodnot ve sloupci : P - příjem, V - výdaj, X - převod, I - investice
            záleží na hodnotě a charakteru účtu např. vklad na kreditní kartu je výdaj
        """
        try:
            hodnota_categid = p_transakce.get('CATEGID', 0)
            if hodnota_categid > 0:
                if self.dfKategorie.loc[p_transakce.CATEGID]['TRANSFER_FLAG'] == 1:
                    return 'X'  # transakce je převod mezi účty - nastaveno  kategorií

            accounttype = self.dfUcty.loc[p_transakce.ACCOUNTID]['ACCOUNTTYPE']

            if accounttype == 'Credit Card':
                if p_transakce.TRANSCODE == 'Withdrawal':
                    return 'V'
                else:
                    return 'X'
            elif accounttype == 'Checking':
                if p_transakce.TRANSCODE == 'Withdrawal':
                    return 'V'
                else:
                    return 'P'
            elif accounttype in ('Term', 'Asset'):
                if p_transakce.TRANSCODE == 'Withdrawal':
                    return 'I'
                else:
                    return 'I'
            elif accounttype == 'Cash':
                if p_transakce.TRANSCODE == 'Withdrawal':
                    return 'V'
                else:
                    return 'X'
            else:
                raise Exception(f'Neznámý typ účtu:{accounttype}')

        except Exception as exc:
            print(f'Error Serie:{p_transakce.to_string()}')
            raise ValueError({exc})

    def prenastav_supertype(self):
        """
        Nastaví sloupec CHECKING_ACCOUNT_V1.SuperType pro včechny pohyby znovu
        """
        print(f"Nastav SuperType pro všechny pohyby znovu")
        statistika_nastaveni = Counter(updated=0, tested=0)
        df_vsechny_pohyby = self.db.query('select * from CHECKINGACCOUNT_V1  order by TRANSID')
        df_vsechny_pohyby.set_index('TRANSID', inplace=True)
        for transid, zaznam_pohyb in df_vsechny_pohyby.iterrows():
            new_supertype = self.compute_super_type(zaznam_pohyb)
            statistika_nastaveni['tested'] += 1
            # různé hodnoty ale pozor na None
            if not (new_supertype == zaznam_pohyb.SUPERTYPE):
                self.db.execute('UPDATE CHECKINGACCOUNT_V1 set SUPERTYPE = :SUPERTYPE where TRANSID=:TRANSID',
                                {'TRANSID': transid, 'SUPERTYPE': new_supertype})
                statistika_nastaveni['updated'] += 1

        if statistika_nastaveni['updated'] > 0:
            self.db.commit()
        print(f'  OK update Statistika: {dict(statistika_nastaveni)}')
