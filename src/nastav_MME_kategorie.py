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
    ('ODCHOZ� PLATBA DO JIN� BANKY:P�EVOD PROST�EDK�:�KOFIN :\'000000-0017145783/0300\':0001130887',
     'Automobil:Spl�tky po��zen�'),
    ('�erp�n� bonus pr�mie', 'P��jmy:Bonus premie'),
    ('P��CHOZ� PLATBA Z MBANK:V�PLATA:.*', 'P��jmy:Mzda'),
    ('P��CHOZ� PLATBA Z MBANK:P�EVOD PROST�EDK�:DAVID N�MEC.*', 'P��jmy:Mzda'),
    ('P��CHOZ� PLATBA Z JIN� BANKY:000043-3920530227/0100:0138:0000000009', 'P��jmy:Mzda'),
    ('INKASO / DD:UPC-.*:000000-0000247273/5400:0308:0045020281', '��ty a faktury:N�jem'),
    ('ODCHOZ� PLATBA .*BANKY:N�JEMN� A Z�LOHY ZA BYT.*000000-0155895339.*', '��ty a faktury:N�jem'),
    ('ODCHOZ� PLATBA .* BANKY:POPLATKY TELEVIZE A ROZHLAS:.*', '��ty a faktury:TV a rozhlas'),
    ('ODCHOZ� PLATBA .* BANKY:POIPLATKY ROZHLAS:�ESK� ROZHLAS POPLATKY.*', '��ty a faktury:TV a rozhlas'),
    ('ODCHOZ� PLATBA .* BANKY:PRE Z�LOHY ELEKT�INA N�MCOVI.*000019-2784000277/0100.*', '��ty a faktury:Elekt�ina'),
    ('ODCHOZ� PLATBA BANKY:STRAVN� MAT�J N�MEC:000000-0131545369/0800:0000002084', 'J�dlo:J�dlo mimo domov'),
    ('.*INKASO / SIPO:GJH:�KOLN� J�DELNA.*', 'J�dlo:J�dlo mimo domov'),
    ('U KRBU', 'J�dlo:J�dlo mimo domov'),
    ('KORUNKA U ARBESA', 'J�dlo:J�dlo mimo domov'),
    ('GOPAY  \*IMPULZY.CZ', 'Vzd�l�n�:Kurzy'),
    ('RANGOLI', 'J�dlo:J�dlo mimo domov'),
    ('TONKIN RESTAURACE', 'J�dlo:J�dlo mimo domov'),
    ('PHO 88 RESTAURACE', 'J�dlo:J�dlo mimo domov'),
    ('GANGSTERBURGER', 'J�dlo:J�dlo mimo domov'),
    ('MARASIL-NOVY SMICHOV', 'J�dlo:J�dlo mimo domov'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:P�EVOD PROST�EDK�:GENERALLI POJI��OVNA.*', 'Poji�t�n�:Domov'),
    ('ODCHOZ� PLATBA BANKY:�IVOTN� POJI�T�N� FLEXI:000000-1210230319/0800:0012883197', 'Poji�t�n�:�ivot'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:N�JEMN� A Z�LOHY ZA BYT:000000-0155895339/0800:0000150104', '��ty a faktury:N�jem'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:POPLATKY TELEVIZE A ROZHLAS:008029-1800060583/0300:0558:8880165467',
     '��ty a faktury:TV a rozhlas'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:SPL�TKA CREDITNI KARTY:000000-8444444047/2600:6400162807', 'P�evod ��et-��et:'),
    ('P�evod do mBank', 'P�evod ��et-��et:'),
    ('.* PROST�EDK� RB TAM-ZP�T.*', 'P�evod ��et-��et:'),
    ('670100-2200593065/6210 DAVID NEMEC P��choz� �hrada', 'P�evod ��et-��et:'),
    ('.*670100-2200593065/6210 DAVID N�MEC P��choz� �hrada', 'P�evod ��et-��et:'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:SPL�TKA KREDITN� KARTY:000000-5160018296/5500:1940350828', 'P�evod ��et-��et:'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:SPL�TKA KREDITN� KARTY:SPL�TKA KREDITN� KARTA RAIFFEISENBANK :.*',
     'P�evod ��et-��et:'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:STRAVN� MAT�J N�MEC:000000-0131545369/0800:0000002084', 'J�dlo:J�dlo mimo domov'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:�IVOTN� POJI�T�N� FLEXI:000000-1210230319/0800:0012883197', 'Poji�t�n�:�ivot'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:�IVOTN� POJI�T�N� FLEXI:.*000000-1210230319/0800.*', 'Poji�t�n�:�ivot'),
    ('POPLATEK ZA .*', '��ty a faktury:Bankovn� poplatky'),
    ('M�sto: POPL. ERA DEBIT MC, ��stka: .* CZK .*', '��ty a faktury:Bankovn� poplatky'),
    ('Sr�kov� da�', '��ty a faktury:Bankovn� poplatky'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:DA� Z NEMOVIT�CH V�C� .*', 'Dan�:Da� z nemovitost�'),
    ('Kladn� �rok', '��ty a faktury:Bankovn� poplatky'),
    ('POPLATEK ZA BAL��EK:POPLATEK - SMS PO SPOT�.P�EDPL', '��ty a faktury:Bankovn� poplatky'),
    ('M�S��N� POPLATEK HL.', '��ty a faktury:Bankovn� poplatky'),
    ('STORNO POPLATKU KARTY', '��ty a faktury:Bankovn� poplatky'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:PRE Z�LOHY ELEKT�INA N�MCOVI:000019-2784000277/0100:0020127161',
     '��ty a faktury:Elekt�ina'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:MAT�J STAVEBN� SPO�EN�:000000-5714627801/7960:0611124459', 'Spo�en�:Mat�j spo�en�'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:MAT�J STAVEBN� SPO�EN�:�MSS STAVEBN� SPO�EN�.*000000-5714627502/7960.*0611124459',
     'Spo�en�:Mat�j spo�en�'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:MAT�J STAVEBN� SPO�EN�:000000-5714627801/7960:0611124459', 'Spo�en�:Mat�j spo�en�'),
    ('ODCHOZ� PLATBA .*�MSS STAVEBN� SPO�EN� DAVID.*000000-1747540405/7960.*7107230207', 'Spo�en�:Stavebn� spo�en�'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:MAT�J STAVEBN� SPO�EN�:000000-5714627502/7960:0611124459', 'Spo�en�:Mat�j spo�en�'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:.*:000000-1747540405/7960:7107230207', 'Spo�en�:Stavebn� spo�en�'),
    ('INKASO / SIPO:DD:UPC-.*000000-0003983815/0300.*', '��ty a faktury:Internet'),
    ('INKASO / SIPO:DD:UPC-.*:000000-0003983815/0300:0308:0045020281.*', '��ty a faktury:Internet'),
    ('VODAFONE CZECH.*', '��ty a faktury:Telefon'),
    ('WWW.O2.SK/DOBIJANIE .*CZK/ EUR', '��ty a faktury:Telefon'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:P�EVOD PROST�EDK� GREENPEACE:GREENPEACE P��SP�VEK.*', 'Z�bava:Dobro�innost'),
    ('ODCHOZ� PLATBA DO JIN� BANKY:P�EVOD PROST�EDK� GREENPEACE:000000-0201123744/0300:0000100744:0000000308',
     'Z�bava:Dobro�innost'),
    ('V�B�R Z BANKOMATU:.*PROVEDEN� TRANSAKCE:.*', 'V�b�r hotovosti:'),
    ('SPL�TKA - 670100-2200593065/6210', 'P�evod ��et-��et:'),
    ('Spl�tka klienta', 'P�evod ��et-��et:'),
    ('P��CHOZ� PLATBA Z JIN� BANKY:P�evod do mBank:Ing. David N�mec :''000000-0646562002/5500''', 'P�evod ��et-��et:'),
    ('LIDL.* PRAHA .* CZ', 'J�dlo:Potraviny'),
    ('Ing. Lubos Kruta', 'J�dlo:Potraviny'),
    ('ALBERT.*', 'J�dlo:Potraviny'),
    ('BENU LEKARNA 060', 'J�dlo:Potraviny'),
    ('DM DROGERIE MARKT.*', 'J�dlo:Potraviny'),
    ('Penny Stefanikova 698', 'J�dlo:Potraviny'),
    ('Tesco Praha Arbesovo n', 'J�dlo:Potraviny'),
    ('PONT THE PARK CHODOV PRAHA 4 CZ', 'J�dlo:Potraviny'),
    ('DOPRAVNI PODNIK HL. M. PRAHA 9 CZ', 'Doprava:MHD a j�zdenky'),
    ('ESHOP.DPP.CZ', 'Doprava:MHD a j�zdenky'),
    ('WWW.SAZKAMOBIL.CZ', '��ty a faktury:Telefon'),
    ('VODAFONE CZECH REPUBLI.*', '��ty a faktury:Telefon'),
    ('ALBERT .* PRAHA .* CZ', 'J�dlo:Potraviny'),
    ('LIDL.*', 'J�dlo:Potraviny'),
    ('FRUITISIMO FRESH', 'J�dlo:J�dlo mimo domov'),
    ('PIZZERIA POMODORO', 'J�dlo:J�dlo mimo domov'),
    ('ODPOCIVADLO', 'J�dlo:J�dlo mimo domov'),
    ('LOVING HUT', 'J�dlo:J�dlo mimo domov'),
    ('YVES ROCHER OC CHODOV', 'Dom�cnost:Drogerie'),
    ('GOOGLE \*EA Mobile', 'Z�bava:Po��ta�ov� hry'),
    ('GOOGLE \*Google Play Ap', 'Z�bava:Po��ta�ov� hry'),
    ('PAYPAL \*SPOTIFY', 'Z�bava:Po��ta�ov� hry'),
    ('PAYPAL \*FIFACOIN', 'Z�bava:Po��ta�ov� hry'),
    ('PAYPAL \*ORIGIN.COM', 'Z�bava:Po��ta�ov� hry'),
    ('LEKARNA SLUNCE LISKOVI.*', 'Zdravotn� p��e:L�ky a vitam�ny'),
    ('Dr.Max Lekarna.*', 'Zdravotn� p��e:L�ky a vitam�ny'),
    ('GREEN FACTORY', 'J�dlo:J�dlo mimo domov'),
    ('HOTEL U MARTINA PRAHA', 'J�dlo:J�dlo mimo domov'),
    ('BEERTIME', 'J�dlo:J�dlo mimo domov'),
    ('PRESTO RESTAURANT CHOD', 'J�dlo:J�dlo mimo domov'),
    ('LOKAL BLOK s.r.o.', 'J�dlo:J�dlo mimo domov'),
    ('MCDONALD.*', 'J�dlo:Potraviny'),
    ('PONT THE PARK CHODOV', 'J�dlo:Potraviny'),
    ('NESPRESSO BOUTIQUE', 'J�dlo:Pochutiny a k�va'),
    ('KREDIT INFO', '��ty a faktury:Bankovn� poplatky'),
    ('Z��TOV�N� �ROK�', '��ty a faktury:Bankovn� poplatky'),
    ('PROFI AUTO CZ.*', 'Automobil:Benz�n'),
    ('SHELL.*', 'Automobil:Benz�n'),
    ('COCA-COLA 1802618106', 'J�dlo:Pochutiny a k�va'),
    ('HOME OFFICE', 'J�dlo:Pochutiny a k�va'),
    ('Home Office', 'J�dlo:Pochutiny a k�va'),
    ('DALLMAYR CSOB.*', 'J�dlo:Pochutiny a k�va'),
    ('DELIKOMAT .*', 'J�dlo:Pochutiny a k�va'),
    ('KFC .*', 'J�dlo:J�dlo mimo domov'),
    ('.* MPASS VERIFY', '��ty a faktury:Bankovn� poplatky'),
    ('COOP Trhova Hradska', 'J�dlo:Potraviny'),
    ('COOP DS PJ 11-098', 'J�dlo:Potraviny'),
    ('LEKARNA BARRANDOV', 'Zdravotn� p��e:L�ky a vitam�ny'),
    ('CINEMA CITY.*', 'Z�bava:Atrakce'),
    ('PayU.CZ\*cinemacity.cz', 'Z�bava:Atrakce'),
    ('.*NA DOM�CNOST .*', 'p�evod Anu�ce:'),
    ('MUDR. RUSNAK', 'Zdravotn� p��e:Zuba� a zubn� hygiena'),
    ('Centrum Tresnovka', 'Z�bava:Sport')
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
            or t.CATEGID = (select c.categid from CATEGORY_V1 c where c.CATEGNAME = 'Nezn�m�')
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
             where t.CATEGID = (select c.categid from CATEGORY_V1 c where c.CATEGNAME = 'V�b�r hotovosti')
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
     pro v�echny pohyby na ��tech se stavebn�m spo�en� nastav� kategorii
     stavebn� spo�en� pop�. Mat�jovo
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
     nastav� kategii a podkategorii pro pohyby z a na ��ty se stavebn�m spo�en�m
    """
    print("set_stavebni_sporeni")
    local_stavebni_sporeni_update(curInput, "Spo�en�:Mat�j spo�en�", "Stavebn� spo�en� Mat�j")
    local_stavebni_sporeni_update(curInput, "Spo�en�:Stavebn� spo�en�", "Stavebn� spo�en�")
    print()


def create_CategoryRules(rulePatternCatSubcat):
    # create dictionary from patterns and DB
    # create dictionary item for rule
    CategoryRules = dict()
    # naplneni slovnkiku s pravidly, dotazeni id pro kategorie a subkategorie z db
    for pattern, categname_subcatname in rulePatternCatSubcat:
        if ":" not in categname_subcatname:
            print("Neni kategorie/subkategorie - nenalezen odd�lova�[:] data:" + categname_subcatname)
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
