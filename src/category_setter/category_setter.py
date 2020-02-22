#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
# Name:        nastavi kategorie a transfery v sqlite DB souboru aplikace MME MoneyManagerEx
# -------------------------------------------------------------------------------

import re
import sqlite3
import sys

from src.category_setter.rules_table import rulePatternCatSubcat
from src.utils.common import Reg


def test_exists(cursor, sqlPartFromWhere, name):
    s = "SELECT count(*) FROM {!s}{!r}".format(sqlPartFromWhere, name)
    cursor.execute(s)
    exist = cursor.fetchone()
    if exist is not None:
        if exist[0] > 0:
            return True
    return False


def get_first_id(cursor, sqlTableName, sIdName):
    cursor.execute("SELECT max({!s}) FROM {!s}".format(sIdName, sqlTableName))
    exist = cursor.fetchone()
    if exist is None:
        return 1
    else:
        if exist[0] is None:
            return 1
        else:
            return exist[0] + 1


# najde ID z DB pro nazev kategorie a podkategorie
def find_categid_subcategid(cursor, categname, subcategname):
    if not subcategname:
        data = cursor.execute("""select categid, subcategid from v_categ_subcateg where categname=?""", [categname])
    else:
        data = cursor.execute(
            """select categid, subcategid from v_categ_subcateg where categname=? and subcategname=?""",
            (categname, subcategname))
    rows = data.fetchall()
    if len(rows) == 0:
        print(
            "No data found in table v_categ_subcateg " + " for categname:" + categname + " subcategname:" + subcategname)
        sys.exit(-1)
    if len(rows) == 1:
        row = rows[0]
        return row['categid'], row['subcategid']
    if len(rows) > 1:
        print(
            "Too many rows found in table v_categ_subcateg" + " for categname:" + categname + " subcategname:" + subcategname)
        sys.exit(-1)


def set_category_by_rules(CategoryRules, curInput, curUpdate):
    print("set_category_by_rules")
    # iterate candidate from DB for update
    iUpd = 0
    iCnt = 0
    data = curInput.execute("""
        select t.*
          from CHECKINGACCOUNT_V1 t
         where t.CATEGID is null
            or t.CATEGID = (select c.categid from CATEGORY_V1 c where c.CATEGNAME = 'Neznámá')
         order by transdate desc
        """)
    #     print(curInput.description)
    for row in data.fetchall():
        r = Reg(curInput, row)
        iCnt += 1
        # check if rule can match
        #         print(row)
        for rule in CategoryRules.values():
            bMatch = False
            if re.search(rule['pattern'], r.NOTES):
                bMatch = True
            if bMatch:
                curUpdate.execute("update CHECKINGACCOUNT_V1 set categid=?, subcategid=? where transid=?",
                                  (rule['categid'], rule['subcatid'], r.TRANSID))
                if curUpdate.rowcount > 0:
                    iUpd += 1
    print("  Uncategorized rows:", iCnt)
    print("  Updated       rows:", iUpd)
    print()


def set_transfers(curInput, curUpdate):
    print("set_transfers")
    # iterate candidate from DB for update
    iUpd = 0
    iCnt = 0

    data = curInput.execute("""
        select t.TRANSID, t.notes, t.TRANSCODE
            from CHECKINGACCOUNT_V1 t
             where t.CATEGID = (select c.categid from CATEGORY_V1 c where c.CATEGNAME = 'Výběr hotovosti')
              and t.transcode <> 'Transfer'
            order by transdate desc
        """)
    for row in data.fetchall():
        r = Reg(curInput, row)
        iCnt += 1
        curUpdate.execute("""update CHECKINGACCOUNT_V1
         set transcode='Transfer',
              toaccountid=(select accountid from ACCOUNTLIST_V1 a where ACCOUNTNAME = 'Hotovost'),
              payeeid=-1,
             subcategid=-1 ,
             totransamount=transamount
           where transid=""" + str(r.TRANSID))
        iUpd += 1

    print("  Uncategorized rows:", iCnt)
    print("  Updated       rows:", iUpd)
    print()


def exec_print_upd_num(curUpdate, msg_text, exec_sql):
    curUpdate.execute(exec_sql)
    if curUpdate.rowcount:
        print(msg_text, curUpdate.rowcount)


def set_payees(curUpdate):
    exec_print_upd_num(curUpdate, "set_payees DEFAULT=1",
                       """update CHECKINGACCOUNT_V1 
                             set PAYEEID = 1 
                           where PAYEEID is null or PAYEEID <> 1""")


def local_stavebni_sporeni_update(curInput, callName, accountName):
    """
     pro všechny pohyby na účtech se stavebním spoření nastaví kategorii
     stavební spoření popř. Matějovo
    """
    print("  " + callName)
    categname, subcatname = callName.split(":")
    categid, subcatid = find_categid_subcategid(curInput, categname, subcatname)
    curInput.execute("""
       UPDATE CHECKINGACCOUNT_V1
          SET CATEGID=?, SUBCATEGID=?
        where ACCOUNTID = (select a.ACCOUNTID from ACCOUNTLIST_V1 a where a.ACCOUNTNAME = ?)
          AND (CATEGID<>? or SUBCATEGID<>?)
        """, (categid, subcatid, accountName, categid, subcatid))
    iUpd = curInput.rowcount
    print("  Updated category rows:", iUpd)

    curInput.execute("""
       UPDATE CHECKINGACCOUNT_V1
        SET transcode='Transfer',
              toaccountid=(select accountid from ACCOUNTLIST_V1 a where ACCOUNTNAME = ?),
              payeeid=-1,
             totransamount=transamount
        where
          CATEGID= ?
          AND SUBCATEGID =?
          AND transcode not in ('Transfer')
          AND  accountid <> (select accountid from ACCOUNTLIST_V1 a where ACCOUNTNAME = ?)
        """, (accountName, categid, subcatid, accountName))
    iUpd = curInput.rowcount
    print("  Updated  to transfer rows:", iUpd)


def set_stavebni_sporeni(curInput):
    """
     nastaví kategii a podkategorii pro pohyby z a na účty se stavebním spořením
    """
    print("set_stavebni_sporeni")
    local_stavebni_sporeni_update(curInput, "Spoření:Matěj spoření", "Stavební spoření Matěj")
    local_stavebni_sporeni_update(curInput, "Spoření:Stavební spoření", "Stavební spoření")
    print()


def create_CategoryRules(rulePatternCatSubcat, curInput):
    # create dictionary from patterns and DB
    # create dictionary item for rule
    CategoryRules = dict()
    # naplneni slovnkiku s pravidly, dotazeni id pro kategorie a subkategorie z db
    for pattern, categname_subcatname in rulePatternCatSubcat.items():
        if ":" not in categname_subcatname:
            print("Neni kategorie/subkategorie - nenalezen oddělovač[:] data:" + categname_subcatname)
            sys.exit(-1)
        categname, subcatname = categname_subcatname.split(":")
        categid, subcatid = find_categid_subcategid(curInput, categname, subcatname)
        row = {'pattern': pattern, 'categname': categname, 'subcategname': subcatname, 'categid': categid,
               'subcatid': subcatid}
        CategoryRules[pattern] = row
    #         print(row)
    print("CategoryRules:" + str(len(CategoryRules.items())))
    print()
    return CategoryRules


class CategorySetter(object):

    def set_categories(filename):
        print(f"Soubor:{filename}")

        connInput = sqlite3.connect(filename)
        # connInput.set_trace_callback(print)
        connInput.row_factory = sqlite3.Row
        curInput = connInput.cursor()
        curUpdate = connInput.cursor()

        CategoryRules = create_CategoryRules(rulePatternCatSubcat, curInput)

        set_category_by_rules(CategoryRules, curInput, curUpdate)
        set_stavebni_sporeni(curInput)
        set_transfers(curInput, curUpdate)
        set_payees(curUpdate)
        connInput.commit()
        print("Done.")
