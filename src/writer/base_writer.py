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
    """ Implementuje z�pis do MMX datab�ze sqlite"""

    def __init__(self, p_db: SqliteDatabase):
        self.db = p_db
        # na�ten� nem�n�nn�ch tabulek do pam�ti
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
        print_frame(result, '\n* Kandid�ti na pravidlo *', '   ')

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

            # odstra� ��dky p�ed datem posledn�ho importu
            df_csv_radky = df_csv_radky[df_csv_radky['Datum'] >= str_datum_posl_pohyb_na_ucte]

            # kopie pr�zdn� struktury
            nove_vkladane_radky = pd.DataFrame(data=None, columns=df_existujici_pohyby.columns,
                                               index=None)
            nove_vkladane_radky.index.names = df_existujici_pohyby.index.names

            for index, row in df_csv_radky.iterrows():
                # najdi existuj�c� z�znamy se stejn�mi hodnotami na stejn�m ��tu
                dict_values = dict(
                    ACCOUNTID=accountid, TOACCOUNTID=-1, PAYEEID=1,
                    TRANSCODE=row['Operace'], TRANSAMOUNT=row['��stka'], STATUS=df_ucet_info.ACCOUNTNAME.values[0],
                    TRANSACTIONNUMBER=row['ID transakce'], NOTES=row['Pozn�mka'].strip(), TRANSDATE=row['Datum'],
                    FOLLOWUPID=-1, TOTRANSAMOUNT=0, TRANSID=None, CATEGID=CATEGID_NEZNAMA, SUBCATEGID=None, SUPERTYPE=None)

                df_stejne = df_existujici_pohyby[(df_existujici_pohyby["ACCOUNTID"] == accountid)
                                                 & (df_existujici_pohyby["TRANSDATE"] == dict_values['TRANSDATE'])
                                                 & (df_existujici_pohyby["TRANSAMOUNT"] == dict_values['TRANSAMOUNT'])
                                                 & ((df_existujici_pohyby["TRANSCODE"] == dict_values['TRANSCODE']) |
                                                    df_existujici_pohyby["TRANSCODE"].str.startswith('Transfer'))]
                #  pokud je v�ce a existuje ��slo transakce p�id�me do filtru
                if len(df_stejne.index) > 1 & len(str(row['ID transakce'])) > 0:
                    df_stejne = df_stejne[
                        (df_existujici_pohyby["TRANSACTIONNUMBER"] == row['ID transakce'])]

                if len(df_stejne.index) > 1 & len(row['Pozn�mka']) > 0:
                    df_stejne = df_stejne[(df_existujici_pohyby["NOTES"].str.startswith(row['Pozn�mka']))]

                if len(df_stejne.index) == 0:  # nov� hodnota pro vlo�en�
                    print(f'Insert {str(dict_values)}')
                    nove_vkladane_radky = nove_vkladane_radky.append(dict_values, ignore_index=True)
                elif len(df_stejne.index) == 1:  # OK existuje ji� pr�v� jeden v DB
                    pass
                else:
                    # vyj�mka n�kup v automatu 2x stejn� den stejn� polo�ka , nebyly ��sla transakc� tehd�...
                    if dict_values.get('ACCOUNTID', 0) == 11 \
                            and dict_values.get('NOTES', 0) == 'PLATBA KARTOU:OVI STORE /HELSINKI' \
                            and row.TRANSDATE == '2010-05-03':
                        #     vyj�mka dva stejn� pohyby v 1 den stejn� ��stka i pozn�mka historii mBank nelze rozli�it
                        pass
                    else:
                        raise Exception(
                            f'Existuje {len(df_stejne.index)} z�znam� v ��tu:'
                            f'{accountid}-{df_ucet_info.ACCOUNTNAME.values[0]} pro zdrojov�:{str(row)}')

            if len(nove_vkladane_radky.index):
                print(f'Celkem pro INSERT hodnot: {len(nove_vkladane_radky.index)}')
                nove_vkladane_radky.to_sql('CHECKINGACCOUNT_V1', self.db.connection(), if_exists='append', index=False)
                self.db.commit()

    def compute_super_type(self, p_transakce: Series):
        """Spo�te Supertyp z pohybu a druhu ��tu
                 slo�it� rozhodov�n� jak nastavit sloupec SUPERTYPE
            v�znam hodnot ve sloupci : P - p��jem, V - v�daj, X - p�evod, I - investice
            z�le�� na hodnot� a charakteru ��tu nap�. vklad na kreditn� kartu je v�daj
        """
        try:
            hodnota_categid = p_transakce.get('CATEGID', 0)
            if hodnota_categid > 0:
                if self.dfKategorie.loc[p_transakce.CATEGID]['TRANSFER_FLAG'] == 1:
                    return 'X'  # transakce je p�evod mezi ��ty - nastaveno  kategori�

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
                raise Exception(f'Nezn�m� typ ��tu:{accounttype}')

        except Exception as exc:
            print(f'Error Serie:{p_transakce.to_string()}')
            raise ValueError({exc})

    def prenastav_supertype(self):
        """
        Nastav� sloupec CHECKING_ACCOUNT_V1.SuperType pro v�echny pohyby znovu
        """
        print(f"Nastav SuperType pro v�echny pohyby znovu")
        statistika_nastaveni = Counter(updated=0, tested=0)
        df_vsechny_pohyby = self.db.query('select * from CHECKINGACCOUNT_V1  order by TRANSID')
        df_vsechny_pohyby.set_index('TRANSID', inplace=True)
        for transid, zaznam_pohyb in df_vsechny_pohyby.iterrows():
            new_supertype = self.compute_super_type(zaznam_pohyb)
            statistika_nastaveni['tested'] += 1
            # r�zn� hodnoty ale pozor na None
            if not (new_supertype == zaznam_pohyb.SUPERTYPE):
                self.db.execute('UPDATE CHECKINGACCOUNT_V1 set SUPERTYPE = :SUPERTYPE where TRANSID=:TRANSID',
                                {'TRANSID': transid, 'SUPERTYPE': new_supertype})
                statistika_nastaveni['updated'] += 1

        if statistika_nastaveni['updated'] > 0:
            self.db.commit()
        print(f'  OK update Statistika: {dict(statistika_nastaveni)}')
