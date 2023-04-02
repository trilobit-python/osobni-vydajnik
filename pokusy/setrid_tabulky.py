#!/usr/bin/env python3
# -*- coding: windows-1250 -*-
#
# VYp�e po�ad� tabulek v po�ad� v jak�m lze prov�st INSERTy
#   - vstupem je seznam tabulek odd�len� ��rkou a seznam z�vislost� tabulka-FK_tabulka odd�len� ��rtkou
#
import re


def seznam_z_retezce(seznam_hodnot: str, oddelovac: str = ','):
    """Odstran� mezery a vr�t� seznam hodnot z �et�zce rozd�len�ch dle odd�lova�e"""
    bez_mezer = re.sub(r"\s+", "", seznam_hodnot, flags=re.UNICODE)
    if len(bez_mezer):
        return bez_mezer.split(oddelovac)
    return []


def serad_tabulky(csv_tabulky: str, csv_tabulka_X_fk_tabulka: str):
    seznam_tabulek = seznam_z_retezce(csv_tabulky)
    seznam_zavislost� = seznam_z_retezce(csv_tabulka_X_fk_tabulka)

    #  napln�n� slovn�ku tabulka-seznam_fk_tabulek
    slovnik_vstup = {}
    for tabulka in seznam_tabulek:
        slovnik_vstup[tabulka] = []

    for zavislost in seznam_zavislost�:
        zdroj, fk_tabulka = zavislost.split('-')
        slovnik_vstup[zdroj].append(fk_tabulka)

    print(f'Tabulky: {seznam_tabulek} ', end='')
    print(f' Zavislosti: {seznam_zavislost�}', end='')
    # print(slovnik_vstup)
    max_pocet_iteraci = len(seznam_tabulek)
    cislo_iterace = 0
    seznam_vystup = []
    while cislo_iterace < max_pocet_iteraci and len(slovnik_vstup):
        seznam_kola = []
        # v�echny z�znamy bez FK lze p�esunout
        for zdroj in slovnik_vstup:
            if len(slovnik_vstup[zdroj]) == 0:
                seznam_kola.append(zdroj)
        # presunout ze seznamu kola do v�sledku
        seznam_vystup += seznam_kola
        # smazat ty co �li do v�stupu
        for odstranit in seznam_kola:
            del slovnik_vstup[odstranit]
        # smazat n�zvy p�esunut� z FK tabulek, ji� existuj�
        for presunuta in seznam_kola:
            for zdroj in slovnik_vstup:
                if presunuta in slovnik_vstup[zdroj]:
                    slovnik_vstup[zdroj].remove(presunuta)

        cislo_iterace += 1

    if cislo_iterace == max_pocet_iteraci:
        raise ValueError('Cyklick� odkaz mezi tabulkami nem� �e�en�')

    vysledek = ','.join(seznam_vystup)
    print(f' V�sledek:{vysledek}')
    return vysledek


# serad_tabulky('t1,t2,t3', 't1-t2,t2-t3,t3-t1')
# serad_tabulky('t1,t2,t3', '')
# serad_tabulky('t1,t2,t3', 't1-t3')
