#!/usr/bin/env python
# -*- coding: windows-1250 -*-
import pandas
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.readers.base_reader import xReader
from src.sqlite.mmx_db_utils import getACCOUNTID
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

        # příprava načtení definic účtů do DataFrame dfUcty
        self.dfUcty = pandas.read_sql('select * from ACCOUNTLIST_V1 order by 1', self.engine)
        self.dfUcty.set_index('ACCOUNTID', inplace=True)
        self.dfKategorie = pandas.read_sql('select * from CATEGORY_V1 order by 1', self.engine)
        self.dfKategorie.set_index('CATEGID', inplace=True)

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
        # from sqlalchemy import or_
        # filter(or_(User.name == 'leela', User.name == 'akshay'))
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
                    CHECKINGACCOUNTV1.TRANSCODE.in_([vydaj.TRANSCODE, 'Transfer']),
                    CHECKINGACCOUNTV1.TRANSACTIONNUMBER == vydaj.TRANSACTIONNUMBER).count()
                if n_s_poznamkou == 1:
                    n_exists = 1

        if n_exists > 1:
            if len(vydaj.NOTES) > 0:
                n_s_poznamkou = self.session.query(CHECKINGACCOUNTV1.TRANSID).filter(
                    CHECKINGACCOUNTV1.ACCOUNTID == self.accID,
                    CHECKINGACCOUNTV1.TRANSDATE == vydaj.TRANSDATE,
                    CHECKINGACCOUNTV1.TRANSAMOUNT == vydaj.TRANSAMOUNT,
                    CHECKINGACCOUNTV1.TRANSCODE.in_([vydaj.TRANSCODE, 'Transfer']),
                    CHECKINGACCOUNTV1.NOTES.like(vydaj.NOTES + '%')).count()
                if n_s_poznamkou == 1:
                    n_exists = 1

        if n_exists > 1:
            if len(vydaj.NOTES) > 0:
                n_s_poznamkou = self.session.query(CHECKINGACCOUNTV1.TRANSID).filter(
                    CHECKINGACCOUNTV1.ACCOUNTID == self.accID,
                    CHECKINGACCOUNTV1.TRANSDATE == vydaj.TRANSDATE,
                    CHECKINGACCOUNTV1.TRANSAMOUNT == vydaj.TRANSAMOUNT,
                    CHECKINGACCOUNTV1.TRANSCODE.in_([vydaj.TRANSCODE, 'Transfer']),
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

    def ComputeSuperType(self, p_transakce: CHECKINGACCOUNTV1):
        '''Spočte Supertyp z pohybu a druhu účtu
                 složité rozhodování jak nastavit sloupec SUPERTYPE
            význam hodnot ve sloupci : P - příjem, V - výdaj, X - převod, I - investice
            záleží na hodnotě a charakteru účtu např. vklad na kreditní kartu je výdaj
        '''
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
            elif ACCOUNTTYPE == 'Term':
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
            new_supertype = self.ComputeSuperType(row)
            if new_supertype != row.SUPERTYPE:
                row.SUPERTYPE = new_supertype
                n_updated += 1
                n_unassigned += 1

        if n_updated:
            self.session.commit()

        print(f'OK Update:{n_updated} of {n_unassigned}')
        print()
