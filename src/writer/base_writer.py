#!/usr/bin/env python
# -*- coding: windows-1250 -*-
import sqlite3
import sys
import traceback

import pandas
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.readers.base_reader import xReader
from src.sqlite.sqlalchemy_declarative import Base, CHECKINGACCOUNTV1
from src.utils.common import print_frame
from src.writer.category_setter import CategorySetter


class xWriter:
    """ Implementuje zápis do MMX databáze sqlite"""

    def __init__(self, sqlite_file: str):
        self.db_file = f'sqlite:///{sqlite_file}'
        # engine = create_engine( db_file, echo=True)
        self.engine = create_engine(self.db_file)
        Base.metadata.bind = self.engine
        session = sessionmaker(bind=self.engine)
        session.configure(bind=self.engine)
        self.session = session()

        try:
            self.conn = sqlite3.connect(sqlite_file)
            self.cur = self.conn.cursor()
            print('OK sqlite3 connect')
        except sqlite3.Error as er:
            # raise ValueError(f'Failed to connect to database! {sqlite3.Error}')
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))
            raise ValueError(f'Failed to connect to database!')

        # příprava načtení definic účtů do DataFrame dfUcty
        self.dfUcty = pandas.read_sql('select * from ACCOUNTLIST_V1 order by 1', self.conn)
        self.dfUcty.set_index('ACCOUNTID', inplace=True)
        self.dfKategorie = pandas.read_sql('select * from CATEGORY_V1 order by 1', self.conn)
        self.dfKategorie.set_index('CATEGID', inplace=True)

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
        setter = CategorySetter(self.session, root_dir_trans_hist, self.cur)
        setter.set_categories()

    def show_rule_candidates(self):
        sql_txt = '''
            SELECT NOTES, Pocet, SumCastka, MinDate, MaxDate
              from v_statistika_bez_kategorie
             where pocet > 1
             order by pocet desc
        '''
        result = pandas.read_sql_query(sql_txt, self.engine)
        print_frame(pandas, result, '\n* Kandidáti na pravidlo *')

    def zapis_do_db(self, reader: xReader):
        df_ucet_info = pd.read_sql_query('select * from ACCOUNTLIST_V1 where ACCOUNTNAME = :name ',
                                         self.conn, index_col=['ACCOUNTID'],
                                         params={'name': reader.accName})

        if len(df_ucet_info.index):
            # zapis DataFrame z readeru do DB
            accountid = int(df_ucet_info.index[0])
            df_existujici_pohyby = pd.read_sql_query('select * from CHECKINGACCOUNT_V1 where ACCOUNTID = :id',
                                                     self.conn,
                                                     index_col=['TRANSID'],
                                                     params={'id': accountid}
                                                     )
            str_datum_posl_pohyb_na_ucte = '2000-01-01'
            if len(df_existujici_pohyby.index):
                str_datum_posl_pohyb_na_ucte = df_existujici_pohyby.TRANSDATE.max()

            df_csv_radky = reader.get_data_frame()

            # odstraň řádky před datem posledního importu
            df_csv_radky = df_csv_radky[df_csv_radky['Datum'] >= str_datum_posl_pohyb_na_ucte]

            # kopie prázdné struktury
            nove_vkladane_radky = pd.DataFrame(data=None, columns=df_existujici_pohyby.columns,
                                               index=df_existujici_pohyby.index)

            for index, row in df_csv_radky.iterrows():
                # najdi existující záznamy se stejnými hodnotami na stejném účtu
                dict_values = dict(
                    ACCOUNTID=accountid, TOACCOUNTID=-1, PAYEEID=1,
                    TRANSCODE=row['Operace'], TRANSAMOUNT=row['Částka'], STATUS=df_ucet_info.ACCOUNTNAME.values[0],
                    TRANSACTIONNUMBER=row['ID transakce'], NOTES=row['Poznámka'], TRANSDATE=row['Datum'],
                    FOLLOWUPID=-1, TOTRANSAMOUNT=0, TRANSID=None, CATEGID=None, SUBCATEGID=None, SUPERTYPE=None)

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
                    print(f'Insert {str(row.to_dict())}')
                    nove_vkladane_radky = nove_vkladane_radky.append(dict_values, ignore_index=True)
                elif len(df_stejne.index) == 1:  # OK existuje již právě jeden v DB
                    pass
                else:
                    # vyjímka nákup v automatu 2x stejný den stejná položka , nebyly čísla transakcí tehdá...
                    if dict_values.ACCOUNTID == 11 and dict_values.NOTES == 'PLATBA KARTOU:OVI STORE /HELSINKI' and \
                            row.TRANSDATE == '2010-05-03':
                        #     vyjímka dva stejné pohyby v 1 den stejná částka i poznámka historii mBank nelze rozlišit
                        pass
                    else:
                        raise Exception(
                            f'Existuje {len(df_stejne.index)} záznamů v účtu:'
                            f'{accountid}-{df_ucet_info.ACCOUNTNAME.values[0]} pro zdrojový:{str(row)}')

            if len(nove_vkladane_radky.index):
                print(f'Celkem pro INSERT hodnot: {len(nove_vkladane_radky.index)}')
                nove_vkladane_radky.to_sql('CHECKINGACCOUNT_V1', self.conn, if_exists='append', index=False)
                # # vložení nových hodnot do DB
                # sql = ''' INSERT INTO CHECKINGACCOUNT_V1
                #                       (TRANSID, ACCOUNTID, TOACCOUNTID, PAYEEID, TRANSCODE,
                #                        TRANSAMOUNT, STATUS, TRANSACTIONNUMBER, NOTES, CATEGID,
                #                        SUBCATEGID, TRANSDATE, FOLLOWUPID, TOTRANSAMOUNT, SUPERTYPE)
                #           VALUES (:TRANSID, :ACCOUNTID, :TOACCOUNTID, :PAYEEID, :TRANSCODE,
                #                   :TRANSAMOUNT, :STATUS, :TRANSACTIONNUMBER, :NOTES, :CATEGID,
                #                   :SUBCATEGID, :TRANSDATE, :FOLLOWUPID, :TOTRANSAMOUNT, :SUPERTYPE)'''
                # self.cur.execute(sql, dict_values)
                # self.conn.rollback()
                self.conn.commit()
                # return cur.lastrowid

        def compute_super_type(self, p_transakce: CHECKINGACCOUNTV1):
            """Spočte Supertyp z pohybu a druhu účtu
                     složité rozhodování jak nastavit sloupec SUPERTYPE
                význam hodnot ve sloupci : P - příjem, V - výdaj, X - převod, I - investice
                záleží na hodnotě a charakteru účtu např. vklad na kreditní kartu je výdaj
            """
            try:
                if p_transakce.CATEGID:
                    TRANSFER_FLAG = self.dfKategorie.loc[p_transakce.CATEGID]['TRANSFER_FLAG']
                    if TRANSFER_FLAG == 1:
                        return 'X'  # transakce je převod mezi účty - nastaveno  kategorií

                ACCOUNTTYPE = self.dfUcty.loc[p_transakce.ACCOUNTID]['ACCOUNTTYPE']

                if ACCOUNTTYPE == 'Credit Card':
                    if p_transakce.TRANSCODE == 'Withdrawal':
                        return 'V'
                    else:
                        return 'X'
                elif ACCOUNTTYPE == 'Checking':
                    if p_transakce.TRANSCODE == 'Withdrawal':
                        return 'V'
                    else:
                        return 'P'
                elif ACCOUNTTYPE in ('Term', 'Asset'):
                    if p_transakce.TRANSCODE == 'Withdrawal':
                        return 'I'
                    else:
                        return 'I'
                elif ACCOUNTTYPE == 'Cash':
                    if p_transakce.TRANSCODE == 'Withdrawal':
                        return 'V'
                    else:
                        return 'X'
                else:
                    raise Exception(f'Neznámý typ účtu:{ACCOUNTTYPE}')

            except Exception as exc:
                print(p_transakce.__dict__)
                print(f' because:{exc}')

        def NastavSuperType(self):
            """Nastaví sloupec CHECKING_ACCOUNT_V1.SuperType
            """
            print(f"  Nastav SuperType pro všechny pohyby")

            n_unassigned, n_updated = 0, 0
            # for row in self.session.query(CHECKINGACCOUNTV1).filter(CHECKINGACCOUNTV1.SUPERTYPE == None). \
            # for row in self.session.query(CHECKINGACCOUNTV1).filter(CHECKINGACCOUNTV1.TRANSID == 8456).order_by(
            #         CHECKINGACCOUNTV1.TRANSDATE): 8456
            for row in self.session.query(CHECKINGACCOUNTV1).order_by(CHECKINGACCOUNTV1.TRANSDATE):
                # print(row.__dict__)
                new_supertype = self.compute_super_type(row)
                if new_supertype != row.SUPERTYPE:
                    row.SUPERTYPE = new_supertype
                    n_updated += 1
                    n_unassigned += 1

            if n_updated:
                self.session.commit()

            print(f'OK Update:{n_updated} of {n_unassigned}')
            print()
