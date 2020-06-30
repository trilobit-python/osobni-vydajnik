#!/usr/bin/env python
# -*- coding: windows-1250 -*-
import pandas
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.category_setter.category_setter import CategorySetter
from src.readers.base_reader import xReader
from src.sqlite.mmx_db_utils import getACCOUNTID
from src.sqlite.sqlalchemy_declarative import Base, CHECKINGACCOUNTV1
from src.utils.common import print_frame


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

    def set_categories(self, root_dir_trans_hist):
        setter = CategorySetter(self.session, root_dir_trans_hist)
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
        self.reader = reader
        self.accID = getACCOUNTID(self.session, reader.accName)
        self.accName = reader.accName

        if self.accID is None:
            return

        if len(self.reader):
            # zapis DataFrame do DB
            pandas.set_option('display.max_colwidth', 128)
            for index, row in self.reader.get_data_frame().iterrows():
                # print(index, row)
                self.merge_to_db(row)

    def row_exists(self, vydaj: CHECKINGACCOUNTV1):
        n_exists = self.session.query(CHECKINGACCOUNTV1.TRANSID) \
            .filter(CHECKINGACCOUNTV1.ACCOUNTID == vydaj.ACCOUNTID,
                    CHECKINGACCOUNTV1.TRANSDATE == vydaj.TRANSDATE,
                    CHECKINGACCOUNTV1.TRANSAMOUNT == vydaj.TRANSAMOUNT,
                    CHECKINGACCOUNTV1.TRANSCODE.in_([vydaj.TRANSCODE, 'Transfer'])).count()
        if n_exists > 1:
            if len(vydaj.TRANSACTIONNUMBER) > 0:
                n_s_poznamkou = self.session.query(CHECKINGACCOUNTV1.TRANSID).filter(
                    CHECKINGACCOUNTV1.ACCOUNTID == self.accID,
                    CHECKINGACCOUNTV1.TRANSDATE == vydaj.TRANSDATE,
                    CHECKINGACCOUNTV1.TRANSAMOUNT == vydaj.TRANSAMOUNT,
                    CHECKINGACCOUNTV1.TRANSACTIONNUMBER == vydaj.TRANSACTIONNUMBER).count()
                if n_s_poznamkou == 1:
                    n_exists = 1

        if n_exists > 1:
            if len(vydaj.NOTES) > 0:
                n_s_poznamkou = self.session.query(CHECKINGACCOUNTV1.TRANSID).filter(
                    CHECKINGACCOUNTV1.ACCOUNTID == self.accID,
                    CHECKINGACCOUNTV1.TRANSDATE == vydaj.TRANSDATE,
                    CHECKINGACCOUNTV1.TRANSAMOUNT == vydaj.TRANSAMOUNT,
                    CHECKINGACCOUNTV1.NOTES.like(vydaj.NOTES + '%')).count()
                if n_s_poznamkou == 1:
                    n_exists = 1

        if n_exists > 1:
            if len(vydaj.NOTES) > 0:
                n_s_poznamkou = self.session.query(CHECKINGACCOUNTV1.TRANSID).filter(
                    CHECKINGACCOUNTV1.ACCOUNTID == self.accID,
                    CHECKINGACCOUNTV1.TRANSDATE == vydaj.TRANSDATE,
                    CHECKINGACCOUNTV1.TRANSAMOUNT == vydaj.TRANSAMOUNT,
                    CHECKINGACCOUNTV1.NOTES.like(vydaj.NOTES[0:39] + '%')).count()
                if n_s_poznamkou == 1:
                    n_exists = 1

        return n_exists

    def merge_to_db(self, row):
        # platce_prijemce = row['Plátce/Příjemce']
        new_vydaj = CHECKINGACCOUNTV1(
            ACCOUNTID=self.accID, TOACCOUNTID=-1, PAYEEID=1,
            TRANSCODE=row['Operace'], TRANSAMOUNT=row['Částka'], STATUS=self.accName,
            TRANSACTIONNUMBER=row['ID transakce'], NOTES=row['Poznámka'], TRANSDATE=row['Datum'],
            FOLLOWUPID=-1, TOTRANSAMOUNT=0)

        n_exists = self.row_exists(new_vydaj)

        if n_exists == 0:
            text: str = 'INS date:{} amount:{} trans:{} note:{}' \
                .format(new_vydaj.TRANSDATE, new_vydaj.TRANSAMOUNT, new_vydaj.TRANSACTIONNUMBER, new_vydaj.NOTES)
            print(self.__class__.__name__, text)
            self.session.add(new_vydaj)
            self.session.flush()
            self.session.commit()

        elif n_exists == 1:  # OK existuje již právě jeden v DB            
            pass

        else:  # print('Divny stav existuje vice nez 1 v DB')
            raise Exception(
                f'Existuje {n_exists} záznamů v účtu:{self.accID}-{self.accName} pro zdrojový:{str(row)}')
            # print(f'Existuje {n_exists} záznamů v účtu:{self.accID}-{self.accName} pro zdrojový:{str(row)}')
