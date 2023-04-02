#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
# Name: nastavi kategorie a transfery v sqlite DB souboru aplikace MME MoneyManagerEx
# -------------------------------------------------------------------------------

import csv
import os
import re
import sys
from collections import Counter

import pandas

from .konstanty import CATEGID_NEZNAMA
from ..utils.sqlite_database import SqliteDatabase


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
            # kontrola �e je to  platn� regul�rn� v�raz
            try:
                re.compile(row['pattern'])
                self.rulePatternCatSubcat[pattern] = categ_sub
            except re.error:
                raise ValueError(f"CategorySetter - neplatny regexp:{row['pattern']}")

        print(f'Na�teno {len(self.rulePatternCatSubcat)} pravidel ze souboru {fname}')

    def spust_potvrd_tiskni(self, sql_dotaz, parametry, text_aktualizace: str):
        c = self.db.execute(sql_dotaz, parametry)
        if c.rowcount > 0:
            self.db.commit()
            print(f"  {text_aktualizace}: {c.rowcount}")

    def set_categories(self):
        category_rules = dict()
        # naplneni slovnkiku s pravidly, dotazeni id pro kategorie a subkategorie z db
        for pattern, cely_nazev_kategorie in self.rulePatternCatSubcat.items():
            categid = self.najdi_celou_kategorii(cely_nazev_kategorie)
            if categid:
                row = {'pattern': pattern, 'categname': cely_nazev_kategorie, 'categid': categid}
                category_rules[pattern] = row
        print("CategoryRules:" + str(len(category_rules.items())))
        print()

        self.set_category_by_rules(category_rules)
        self.set_transfers()

    def nastav_prevod_dle_kategorie(self, plny_nazev_kategorie, target_acc_name):
        """
           pro v�echny pohyby kter� maj� nastavou kategorii-podkategorii
           a nejsou z c�lov�ho ��tu
           a nejsou to P�evody nastav� typ pohybu P�evod na zadan� ��et
        """
        print(f"  Nastav p�evod pro kategorii: {plny_nazev_kategorie} na ��et:{target_acc_name}")

        categ_id = self.najdi_celou_kategorii(plny_nazev_kategorie)
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
                    and TRANSCODE != 'Transfer'
        '''
        parametry = {'target_accid': target_accid, 'categ_id': categ_id}
        self.spust_potvrd_tiskni(sql, parametry, 'Nastaven p�evod pro ��dk�')

    def set_transfers(self):
        print("set_transfers HOTOVOST")
        self.nastav_prevod_dle_kategorie('V�b�r hotovosti', 'Hotovost')
        self.nastav_prevod_dle_kategorie('Spo�en�:Mat�j spo�en�', 'Stavebn� spo�en� Mat�j')
        self.nastav_prevod_dle_kategorie('Spo�en�:Stavebn� spo�en�', 'Stavebn� spo�en�')
        self.nastav_prevod_dle_kategorie('Spo�en�:Penzijn� spo�en�', 'Penzijn� spo�en�')

    def najdi_celou_kategorii(self, nazev_cele_kategorie):
        """najde ID z DB pro nazev kategorie a podkategorie
        """
        df_categorie = self.dfPodKategorie[self.dfPodKategorie.CATEGNAME == nazev_cele_kategorie]
        if df_categorie.empty:
            return None
        if len(df_categorie.index) > 1:
            raise Exception(f'Nenalezeno v�ce z�znam� pro kategorie pro n�zev: {nazev_cele_kategorie}')
        categid = df_categorie.index[0]
        return categid

    def set_category_by_rules(self, category_rules):
        """Najde v�echny pohyby bez kategorie(nebo {CATEGID_NEZNAMA}) a pokus� se ji nastavit pomoc� pravidel"""
        print("Set_category_by_rules")
        df_pohyby = self.db.query(
            f'select * from CHECKINGACCOUNT_V1 where CATEGID is NULL or CATEGID = {CATEGID_NEZNAMA} order by TRANSDATE')
        df_pohyby.set_index('TRANSID', inplace=True)
        statistika = Counter()

        for index, row in df_pohyby.iterrows():
            statistika['celkem'] += 1
            for rule in category_rules.values():
                if re.search(rule['pattern'], row.NOTES):
                    statistika['aktualizovano'] += 1
                    sql_upd = 'update CHECKINGACCOUNT_V1 set CATEGID = :categid ' \
                              ' where TRANSID = :transid'
                    data = {'categid': rule['categid'], 'transid': index}
                    self.db.execute(sql_upd, data)

        # print('*' * 80)
        # for x in category_rules.values():
        #     if '0003983815' in x['pattern']:
        #         print(x)

        if statistika['aktualizovano'] > 0:
            self.db.commit()

        print(f'OK {dict(statistika)}\n')
