#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
# Name:        nastavi kategorie a transfery v sqlite DB souboru aplikace MME MoneyManagerEx
# -------------------------------------------------------------------------------

import csv
import os
import re
import sys

import pandas
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from src.sqlite.mmx_db_utils import getACCOUNTID
from src.sqlite.sqlalchemy_declarative import CATEGORYV1, SUBCATEGORYV1, CHECKINGACCOUNTV1


class CategorySetter(object):
    def __init__(self, p_session, root_dir_trans_hist, p_cur):
        self.session = p_session
        self.cur = p_cur
        fname = os.path.join(root_dir_trans_hist, 'rules.csv')
        rows = pandas.read_csv(fname, delimiter=chr(9), encoding='cp1250', quoting=csv.QUOTE_NONE)

        self.rulePatternCatSubcat = {}  # pattern, categname:subcatname

        for i, row in rows.iterrows():
            pattern = row['pattern']
            categ_sub = row['categname:subcatname']
            if pattern in self.rulePatternCatSubcat:
                print(f"Duplicitní definice pravidla:{pattern}")
                sys.exit(-1)
            else:
                self.rulePatternCatSubcat[pattern] = categ_sub

        print(f'Načteno {len(self.rulePatternCatSubcat)} pravidel ze souboru {fname}')

    def set_categories(self):
        CategoryRules = dict()
        # naplneni slovnkiku s pravidly, dotazeni id pro kategorie a subkategorie z db
        for pattern, categname_subcatname in self.rulePatternCatSubcat.items():
            if ":" not in categname_subcatname:
                print("Neni kategorie/subkategorie - nenalezen oddělovač[:] data:" + categname_subcatname)
                sys.exit(-1)
            categname, subcatname = categname_subcatname.split(":")
            categid, subcatid = self.find_categid_subcategid(categname, subcatname)
            if categid is not None:
                row = {'pattern': pattern, 'categname': categname, 'subcategname': subcatname, 'categid': categid,
                       'subcatid': subcatid}
                CategoryRules[pattern] = row
        print("CategoryRules:" + str(len(CategoryRules.items())))
        print()

        self.set_category_by_rules(CategoryRules)
        self.set_transfers()

    def nastav_prevod_dle_kategorie(self, categ_name, subcateg_name, target_acc_name):
        """
           pro všechny pohyby které mají nastavou kategorii-podkategorii
           a nejsou z cílového účtu
           a nejsou to Převody nastaví typ pohybu Převod na zadaný účet
        """
        print(f"  Nastav převod pro kategorii: {categ_name} pod kategorii:{subcateg_name} na účet:{target_acc_name}")

        categ_id, subcat_id = self.find_categid_subcategid(categ_name, subcateg_name)
        if categ_id is None:
            print("    Neexistuje kategorie")
            return

        target_accid = getACCOUNTID(self.cur, target_acc_name)
        if target_accid is None:
            print("    Neexistuje účet")
            return

        iUpd = self.session.query(CHECKINGACCOUNTV1). \
            filter(CHECKINGACCOUNTV1.ACCOUNTID != target_accid,
                   CHECKINGACCOUNTV1.CATEGID == categ_id,
                   CHECKINGACCOUNTV1.SUBCATEGID == subcat_id,
                   CHECKINGACCOUNTV1.TRANSCODE != 'Transfer'). \
            update(
            {'TRANSCODE': 'Transfer', 'TOACCOUNTID': target_accid, 'PAYEEID': -1,
             'TOTRANSAMOUNT': CHECKINGACCOUNTV1.TRANSAMOUNT})
        self.session.commit()
        print("  Nastaven převod pro řádků:", iUpd)

    def set_transfers(self):
        print("set_transfers HOTOVOST")
        self.nastav_prevod_dle_kategorie('Výběr hotovosti', None, 'Hotovost')
        self.nastav_prevod_dle_kategorie('Spoření', 'Matěj spoření', 'Stavební spoření Matěj')
        self.nastav_prevod_dle_kategorie('Spoření', 'Stavební spoření', 'Stavební spoření')
        self.nastav_prevod_dle_kategorie('Spoření', 'Penzijní spoření', 'Penzijní spoření')

    def find_categid_subcategid(self, p_categname, p_subcategname):
        """najde ID z DB pro nazev kategorie a podkategorie"""
        try:
            obj_categorie = self.session.query(CATEGORYV1).filter(CATEGORYV1.CATEGNAME == p_categname).one()
        except NoResultFound:
            return None, None
        except MultipleResultsFound:
            raise Exception(f'Nenalezeno více záznamů pro kategorie pro název: {p_categname}\n{obj_categorie}')

        if p_subcategname == None or p_subcategname == '':
            return obj_categorie.CATEGID, None

        try:
            obj_subcategorie = self.session. \
                query(SUBCATEGORYV1).filter(SUBCATEGORYV1.CATEGID == obj_categorie.CATEGID,
                                            SUBCATEGORYV1.SUBCATEGNAME == p_subcategname).one()
        except NoResultFound:
            return obj_categorie.CATEGID, None
        except MultipleResultsFound:
            raise Exception(
                f'Nenalezeno více záznamů pro pod-kategorie pro název: {p_categname}-{p_subcategname}\n{obj_subcategorie}')

        return obj_subcategorie.CATEGID, obj_subcategorie.SUBCATEGID

    def set_category_by_rules(self, CategoryRules):
        print("Set_category_by_rules")

        n_unassigned, n_updated = 0, 0
        for row in self.session.query(CHECKINGACCOUNTV1).filter(CHECKINGACCOUNTV1.CATEGID == None). \
                order_by(CHECKINGACCOUNTV1.TRANSDATE):

            n_unassigned += 1

            for rule in CategoryRules.values():
                bMatch = False
                if re.search(rule['pattern'], row.NOTES):
                    bMatch = True
                if bMatch:
                    row.CATEGID = rule['categid']
                    row.SUBCATEGID = rule['subcatid']
                    n_updated += 1

        if n_updated:
            self.session.commit()

        print(f'OK Update:{n_updated} of {n_unassigned}')
        print()
