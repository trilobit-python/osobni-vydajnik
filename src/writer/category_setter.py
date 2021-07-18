#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
# Name:        nastavi kategorie a transfery v sqlite DB souboru aplikace MME MoneyManagerEx
# -------------------------------------------------------------------------------

import csv
import os
import re
import sys
from collections import Counter

import pandas

from src.utils.sqlite_database import SqliteDatabase


class CategorySetter(object):
    def __init__(self, root_dir_trans_hist, p_db: SqliteDatabase, p_df_kategorie, p_df_podkategorie, p_df_ucty):
        self.db = p_db
        self.dfKategorie = p_df_kategorie
        self.dfPodKategorie = p_df_podkategorie
        self.dfUcty = p_df_ucty

        fname = os.path.join(root_dir_trans_hist, 'rules.csv')
        rows = pandas.read_csv(fname, delimiter=chr(9), encoding='cp1250', quoting=csv.QUOTE_NONE)

        self.rulePatternCatSubcat = {}  # pattern, categname:subcatname

        for i, row in rows.iterrows():
            pattern = row['pattern']
            categ_sub = row['categname:subcatname']
            if pattern in self.rulePatternCatSubcat:
                print(f"Duplicitn� definice pravidla:{pattern}")
                sys.exit(-1)
            else:
                self.rulePatternCatSubcat[pattern] = categ_sub

        print(f'Na�teno {len(self.rulePatternCatSubcat)} pravidel ze souboru {fname}')

    def spust_potvrd_tiskni(self, sql_dotaz, parametry, text_aktualizace: str):
        c = self.db.execute(sql_dotaz, parametry)
        if c.rowcount > 0:
            self.db.commit()
            print(f"  {text_aktualizace}: {c.rowcount}")

    def set_categories(self):
        category_rules = dict()
        # naplneni slovnkiku s pravidly, dotazeni id pro kategorie a subkategorie z db
        for pattern, categname_subcatname in self.rulePatternCatSubcat.items():
            if ":" not in categname_subcatname:
                print("Neni kategorie/subkategorie - nenalezen odd�lova�[:] data:" + categname_subcatname)
                sys.exit(-1)
            categname, subcatname = categname_subcatname.split(":")
            categid, subcatid = self.find_categid_subcategid(categname, subcatname)
            if categid is not None:
                row = {'pattern': pattern, 'categname': categname, 'subcategname': subcatname, 'categid': categid,
                       'subcatid': subcatid}
                category_rules[pattern] = row
        print("CategoryRules:" + str(len(category_rules.items())))
        print()

        self.set_category_by_rules(category_rules)
        self.set_transfers()

    def nastav_prevod_dle_kategorie(self, categ_name, subcateg_name, target_acc_name):
        """
           pro v�echny pohyby kter� maj� nastavou kategorii-podkategorii
           a nejsou z c�lov�ho ��tu
           a nejsou to P�evody nastav� typ pohybu P�evod na zadan� ��et
        """
        print(f"  Nastav p�evod pro kategorii: {categ_name} pod kategorii:{subcateg_name} na ��et:{target_acc_name}")

        categ_id, subcat_id = self.find_categid_subcategid(categ_name, subcateg_name)
        if categ_id is None:
            print("    Neexistuje kategorie")
            return

        target_accid = self.dfUcty[self.dfUcty.ACCOUNTNAME == target_acc_name].index[0]
        if target_accid is None:
            print("    Neexistuje ��et")
            return

        sql = '''UPDATE CHECKINGACCOUNT_V1
                    set TRANSCODE = 'Transfer', TOACCOUNTID = :target_accid, PAYEEID = -1, TOTRANSAMOUNT = TRANSAMOUNT
                  where ACCOUNTID != :target_accid
                    and CATEGID == :categ_id
                    and SUBCATEGID == :subcat_id
                    and TRANSCODE != 'Transfer'
        '''
        parametry = {'target_accid': target_accid, 'subcat_id': subcat_id, 'categ_id': categ_id}
        self.spust_potvrd_tiskni(sql, parametry, 'Nastaven p�evod pro ��dk�')

    def set_transfers(self):
        print("set_transfers HOTOVOST")
        self.nastav_prevod_dle_kategorie('V�b�r hotovosti', None, 'Hotovost')
        self.nastav_prevod_dle_kategorie('Spo�en�', 'Mat�j spo�en�', 'Stavebn� spo�en� Mat�j')
        self.nastav_prevod_dle_kategorie('Spo�en�', 'Stavebn� spo�en�', 'Stavebn� spo�en�')
        self.nastav_prevod_dle_kategorie('Spo�en�', 'Penzijn� spo�en�', 'Penzijn� spo�en�')

    def find_categid_subcategid(self, p_categname, p_subcategname):
        """najde ID z DB pro nazev kategorie a podkategorie
        """
        df_categorie = self.dfKategorie[self.dfKategorie.CATEGNAME == p_categname]
        if df_categorie.empty:
            return None, None
        if len(df_categorie.index) > 1:
            raise Exception(f'Nenalezeno v�ce z�znam� pro kategorie pro n�zev: {p_categname}')
        categid = df_categorie.index[0]

        df_podcategorie = self.dfPodKategorie[(self.dfPodKategorie.SUBCATEGNAME == p_subcategname)
                                              & (self.dfPodKategorie.CATEGID == categid)]

        if df_podcategorie.empty:
            return categid, None
        if len(df_podcategorie.index) > 1:
            raise Exception(
                f'Nenalezeno v�ce z�znam� pro pod-kategorie pro n�zev: {p_categname}-{p_subcategname}')

        return categid, df_podcategorie.index[0]

    def set_category_by_rules(self, category_rules):
        print("Set_category_by_rules")
        sql = 'select * from CHECKINGACCOUNT_V1 where CATEGID is NULL order by TRANSDATE'
        df_pohyby = self.db.query(sql)
        df_pohyby.set_index('TRANSID', inplace=True)
        statistika = Counter()

        for index, row in df_pohyby.iterrows():
            statistika['celkem'] += 1

            for rule in category_rules.values():
                if re.search(rule['pattern'], row.NOTES):
                    statistika['aktualizovano'] += 1
                    sql_upd = 'update CHECKINGACCOUNT_V1 set CATEGID = :categid, SUBCATEGID = :subcatid' \
                              ' where TRANSID = :transid'
                    data = {'categid': rule['categid'], 'subcatid': rule['subcatid'], 'transid': index}
                    self.db.execute(sql_upd, data)

        if statistika['aktualizovano'] > 0:
            self.db.commit()

        print(f'OK {dict(statistika)}\n')
