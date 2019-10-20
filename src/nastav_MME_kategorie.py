#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
# Name:        nastavi kategorie a transfery v sqlite DB souboru aplikace MME MoneyManagerEx
# -------------------------------------------------------------------------------

import re
import socket
import sqlite3
import sys

from src.utils.common import Reg

########################## parameters start #####################################################################
sRQMoneyEmptyFile = r"..//vydajeMMEX.mmb"

rulePatternCatSubcat = [
    #   pattern, categname:subcatname
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:PŘEVOD PROSTŘEDKŮ:ŠKOFIN :\'000000-0017145783/0300\':0001130887',
     'Automobil:Splátky pořízení'),
    ('Čerpání bonus prémie', 'Příjmy:Bonus premie'),
    ('PŘÍCHOZÍ PLATBA Z MBANK:VÝPLATA:.*', 'Příjmy:Mzda'),
    ('PŘÍCHOZÍ PLATBA Z MBANK:PŘEVOD PROSTŘEDKŮ:DAVID NĚMEC.*', 'Příjmy:Mzda'),
    ('PŘÍCHOZÍ PLATBA Z JINÉ BANKY:000043-3920530227/0100:0138:0000000009', 'Příjmy:Mzda'),
    ('INKASO / DD:UPC-.*:000000-0000247273/5400:0308:0045020281', 'Účty a faktury:Nájem'),
    ('ODCHOZÍ PLATBA .*BANKY:NÁJEMNÉ A ZÁLOHY ZA BYT.*000000-0155895339.*', 'Účty a faktury:Nájem'),
    ('ODCHOZÍ PLATBA .* BANKY:POPLATKY TELEVIZE A ROZHLAS:.*', 'Účty a faktury:TV a rozhlas'),
    ('ODCHOZÍ PLATBA .* BANKY:POIPLATKY ROZHLAS:ČESKÝ ROZHLAS POPLATKY.*', 'Účty a faktury:TV a rozhlas'),
    ('ODCHOZÍ PLATBA .* BANKY:PRE ZÁLOHY ELEKTŘINA NĚMCOVI.*000019-2784000277/0100.*', 'Účty a faktury:Elektřina'),
    ('ODCHOZÍ PLATBA BANKY:STRAVNÉ MATĚJ NĚMEC:000000-0131545369/0800:0000002084', 'Jídlo:Jídlo mimo domov'),
    ('.*INKASO / SIPO:GJH:ŠKOLNÍ JÍDELNA.*', 'Jídlo:Jídlo mimo domov'),
    ('U KRBU', 'Jídlo:Jídlo mimo domov'),
    ('KORUNKA U ARBESA', 'Jídlo:Jídlo mimo domov'),
    ('GOPAY  \*IMPULZY.CZ', 'Vzdělání:Kurzy'),
    ('RANGOLI', 'Jídlo:Jídlo mimo domov'),
    ('TONKIN RESTAURACE', 'Jídlo:Jídlo mimo domov'),
    ('PHO 88 RESTAURACE', 'Jídlo:Jídlo mimo domov'),
    ('GANGSTERBURGER', 'Jídlo:Jídlo mimo domov'),
    ('MARASIL-NOVY SMICHOV', 'Jídlo:Jídlo mimo domov'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:PŘEVOD PROSTŘEDKŮ:GENERALLI POJIŠŤOVNA.*', 'Pojištění:Domov'),
    ('ODCHOZÍ PLATBA BANKY:ŽIVOTNÍ POJIŠTĚNÍ FLEXI:000000-1210230319/0800:0012883197', 'Pojištění:Život'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:NÁJEMNÉ A ZÁLOHY ZA BYT:000000-0155895339/0800:0000150104', 'Účty a faktury:Nájem'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:POPLATKY TELEVIZE A ROZHLAS:008029-1800060583/0300:0558:8880165467',
     'Účty a faktury:TV a rozhlas'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:SPLÁTKA CREDITNI KARTY:000000-8444444047/2600:6400162807', 'Převod účet-účet:'),
    ('Převod do mBank', 'Převod účet-účet:'),
    ('.* PROSTŘEDKŮ RB TAM-ZPĚT.*', 'Převod účet-účet:'),
    ('670100-2200593065/6210 DAVID NEMEC Příchozí úhrada', 'Převod účet-účet:'),
    ('.*670100-2200593065/6210 DAVID NĚMEC Příchozí úhrada', 'Převod účet-účet:'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:SPLÁTKA KREDITNÍ KARTY:000000-5160018296/5500:1940350828', 'Převod účet-účet:'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:SPLÁTKA KREDITNÍ KARTY:SPLÁTKA KREDITNÍ KARTA RAIFFEISENBANK :.*',
     'Převod účet-účet:'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:STRAVNÉ MATĚJ NĚMEC:000000-0131545369/0800:0000002084', 'Jídlo:Jídlo mimo domov'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:ŽIVOTNÍ POJIŠTĚNÍ FLEXI:000000-1210230319/0800:0012883197', 'Pojištění:Život'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:ŽIVOTNÍ POJIŠTĚNÍ FLEXI:.*000000-1210230319/0800.*', 'Pojištění:Život'),
    ('POPLATEK ZA .*', 'Účty a faktury:Bankovní poplatky'),
    ('Místo: POPL. ERA DEBIT MC, Částka: .* CZK .*', 'Účty a faktury:Bankovní poplatky'),
    ('Srážková daň', 'Účty a faktury:Bankovní poplatky'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:DAŇ Z NEMOVITÝCH VĚCÍ .*', 'Daně:Daň z nemovitostí'),
    ('Kladný úrok', 'Účty a faktury:Bankovní poplatky'),
    ('POPLATEK ZA BALÍČEK:POPLATEK - SMS PO SPOTŘ.PŘEDPL', 'Účty a faktury:Bankovní poplatky'),
    ('MĚSÍČNÍ POPLATEK HL.', 'Účty a faktury:Bankovní poplatky'),
    ('STORNO POPLATKU KARTY', 'Účty a faktury:Bankovní poplatky'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:PRE ZÁLOHY ELEKTŘINA NĚMCOVI:000019-2784000277/0100:0020127161',
     'Účty a faktury:Elektřina'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:MATĚJ STAVEBNÍ SPOŘENÍ:000000-5714627801/7960:0611124459', 'Spoření:Matěj spoření'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:MATĚJ STAVEBNÍ SPOŘENÍ:ČMSS STAVEBNÍ SPOŘENÍ.*000000-5714627502/7960.*0611124459',
     'Spoření:Matěj spoření'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:MATĚJ STAVEBNÍ SPOŘENÍ:000000-5714627801/7960:0611124459', 'Spoření:Matěj spoření'),
    ('ODCHOZÍ PLATBA .*ČMSS STAVEBNÍ SPOŘENÍ DAVID.*000000-1747540405/7960.*7107230207', 'Spoření:Stavební spoření'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:MATĚJ STAVEBNÍ SPOŘENÍ:000000-5714627502/7960:0611124459', 'Spoření:Matěj spoření'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:.*:000000-1747540405/7960:7107230207', 'Spoření:Stavební spoření'),
    ('INKASO / SIPO:DD:UPC-.*000000-0003983815/0300.*', 'Účty a faktury:Internet'),
    ('INKASO / SIPO:DD:UPC-.*:000000-0003983815/0300:0308:0045020281.*', 'Účty a faktury:Internet'),
    ('VODAFONE CZECH.*', 'Účty a faktury:Telefon'),
    ('WWW.O2.SK/DOBIJANIE .*CZK/ EUR', 'Účty a faktury:Telefon'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:PŘEVOD PROSTŘEDKŮ GREENPEACE:GREENPEACE PŘÍSPĚVEK.*', 'Zábava:Dobročinnost'),
    ('ODCHOZÍ PLATBA DO JINÉ BANKY:PŘEVOD PROSTŘEDKŮ GREENPEACE:000000-0201123744/0300:0000100744:0000000308',
     'Zábava:Dobročinnost'),
    ('VÝBĚR Z BANKOMATU:.*PROVEDENÍ TRANSAKCE:.*', 'Výběr hotovosti:'),
    ('SPLÁTKA - 670100-2200593065/6210', 'Převod účet-účet:'),
    ('Splátka klienta', 'Převod účet-účet:'),
    ('PŘÍCHOZÍ PLATBA Z JINÉ BANKY:Převod do mBank:Ing. David Němec :''000000-0646562002/5500''', 'Převod účet-účet:'),
    ('LIDL.* PRAHA .* CZ', 'Jídlo:Potraviny'),
    ('Ing. Lubos Kruta', 'Jídlo:Potraviny'),
    ('ALBERT.*', 'Jídlo:Potraviny'),
    ('BENU LEKARNA 060', 'Jídlo:Potraviny'),
    ('DM DROGERIE MARKT.*', 'Jídlo:Potraviny'),
    ('Penny Stefanikova 698', 'Jídlo:Potraviny'),
    ('Tesco Praha Arbesovo n', 'Jídlo:Potraviny'),
    ('PONT THE PARK CHODOV PRAHA 4 CZ', 'Jídlo:Potraviny'),
    ('DOPRAVNI PODNIK HL. M. PRAHA 9 CZ', 'Doprava:MHD a jízdenky'),
    ('ESHOP.DPP.CZ', 'Doprava:MHD a jízdenky'),
    ('WWW.SAZKAMOBIL.CZ', 'Účty a faktury:Telefon'),
    ('VODAFONE CZECH REPUBLI.*', 'Účty a faktury:Telefon'),
    ('ALBERT .* PRAHA .* CZ', 'Jídlo:Potraviny'),
    ('LIDL.*', 'Jídlo:Potraviny'),
    ('FRUITISIMO FRESH', 'Jídlo:Jídlo mimo domov'),
    ('PIZZERIA POMODORO', 'Jídlo:Jídlo mimo domov'),
    ('ODPOCIVADLO', 'Jídlo:Jídlo mimo domov'),
    ('LOVING HUT', 'Jídlo:Jídlo mimo domov'),
    ('YVES ROCHER OC CHODOV', 'Domácnost:Drogerie'),
    ('GOOGLE \*EA Mobile', 'Zábava:Počítačové hry'),
    ('GOOGLE \*Google Play Ap', 'Zábava:Počítačové hry'),
    ('PAYPAL \*SPOTIFY', 'Zábava:Počítačové hry'),
    ('PAYPAL \*FIFACOIN', 'Zábava:Počítačové hry'),
    ('PAYPAL \*ORIGIN.COM', 'Zábava:Počítačové hry'),
    ('LEKARNA SLUNCE LISKOVI.*', 'Zdravotní péče:Léky a vitamíny'),
    ('Dr.Max Lekarna.*', 'Zdravotní péče:Léky a vitamíny'),
    ('GREEN FACTORY', 'Jídlo:Jídlo mimo domov'),
    ('HOTEL U MARTINA PRAHA', 'Jídlo:Jídlo mimo domov'),
    ('BEERTIME', 'Jídlo:Jídlo mimo domov'),
    ('PRESTO RESTAURANT CHOD', 'Jídlo:Jídlo mimo domov'),
    ('LOKAL BLOK s.r.o.', 'Jídlo:Jídlo mimo domov'),
    ('MCDONALD.*', 'Jídlo:Potraviny'),
    ('PONT THE PARK CHODOV', 'Jídlo:Potraviny'),
    ('NESPRESSO BOUTIQUE', 'Jídlo:Pochutiny a káva'),
    ('KREDIT INFO', 'Účty a faktury:Bankovní poplatky'),
    ('ZÚČTOVÁNÍ ÚROKŮ', 'Účty a faktury:Bankovní poplatky'),
    ('PROFI AUTO CZ.*', 'Automobil:Benzín'),
    ('SHELL.*', 'Automobil:Benzín'),
    ('COCA-COLA 1802618106', 'Jídlo:Pochutiny a káva'),
    ('HOME OFFICE', 'Jídlo:Pochutiny a káva'),
    ('Home Office', 'Jídlo:Pochutiny a káva'),
    ('DALLMAYR CSOB.*', 'Jídlo:Pochutiny a káva'),
    ('DELIKOMAT .*', 'Jídlo:Pochutiny a káva'),
    ('KFC .*', 'Jídlo:Jídlo mimo domov'),
    ('.* MPASS VERIFY', 'Účty a faktury:Bankovní poplatky'),
    ('COOP Trhova Hradska', 'Jídlo:Potraviny'),
    ('COOP DS PJ 11-098', 'Jídlo:Potraviny'),
    ('LEKARNA BARRANDOV', 'Zdravotní péče:Léky a vitamíny'),
    ('CINEMA CITY.*', 'Zábava:Atrakce'),
    ('PayU.CZ\*cinemacity.cz', 'Zábava:Atrakce'),
    ('.*NA DOMÁCNOST .*', 'převod Anušce:'),
    ('MUDR. RUSNAK', 'Zdravotní péče:Zubař a zubní hygiena'),
    ('Centrum Tresnovka', 'Zábava:Sport')
]


########################## parameters end ##########################

def print_data(data):
    print(data.description)
    for row_data in data:
        print(row_data)


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
        return row[0], row[1]
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


def create_CategoryRules(rulePatternCatSubcat):
    # create dictionary from patterns and DB
    # create dictionary item for rule
    CategoryRules = dict()
    # naplneni slovnkiku s pravidly, dotazeni id pro kategorie a subkategorie z db
    for pattern, categname_subcatname in rulePatternCatSubcat:
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


###  MAIN ################

if socket.gethostname() == 'nemecd_nbk':
    sRQMoneyEmptyFile = r"..//vydajeMMEX.mmb"

print("Soubor:" + sRQMoneyEmptyFile)

connInput = sqlite3.connect(sRQMoneyEmptyFile)
curInput = connInput.cursor()
curUpdate = connInput.cursor()

CategoryRules = create_CategoryRules(rulePatternCatSubcat)

set_category_by_rules(CategoryRules, curInput, curUpdate)
set_stavebni_sporeni(curInput)
set_transfers(curInput, curUpdate)
set_payees(curUpdate)
connInput.commit()
# connInput.rollback()
print("Done.")
