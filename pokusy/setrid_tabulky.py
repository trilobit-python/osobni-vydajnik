#!/usr/bin/env python3
# -*- coding: windows-1250 -*-
#
# VYpíše pořadí tabulek v pořadí v jakém lze provést INSERTy
#   - vstupem je seznam tabulek oddělený čárkou a seznam závislostí tabulka-FK_tabulka oddělený čártkou
#
import re


def seznam_z_retezce(seznam_hodnot: str, oddelovac: str = ','):
    """Odstraní mezery a vrátí seznam hodnot z řetězce rozdělených dle oddělovače"""
    bez_mezer = re.sub(r"\s+", "", seznam_hodnot, flags=re.UNICODE)
    if len(bez_mezer):
        return bez_mezer.split(oddelovac)
    return []


def serad_tabulky(csv_tabulky: str, csv_tabulka_X_fk_tabulka: str):
    seznam_tabulek = seznam_z_retezce(csv_tabulky)
    seznam_zavislostí = seznam_z_retezce(csv_tabulka_X_fk_tabulka)

    #  naplnění slovníku tabulka-seznam_fk_tabulek
    slovnik_vstup = {}
    for tabulka in seznam_tabulek:
        slovnik_vstup[tabulka] = []

    for zavislost in seznam_zavislostí:
        zdroj, fk_tabulka = zavislost.split('-')
        slovnik_vstup[zdroj].append(fk_tabulka)

    print(f'Tabulky: {seznam_tabulek} ', end='')
    print(f' Zavislosti: {seznam_zavislostí}', end='')
    # print(slovnik_vstup)
    max_pocet_iteraci = len(seznam_tabulek)
    cislo_iterace = 0
    seznam_vystup = []
    while cislo_iterace < max_pocet_iteraci and len(slovnik_vstup):
        seznam_kola = []
        # všechny záznamy bez FK lze přesunout
        for zdroj in slovnik_vstup:
            if len(slovnik_vstup[zdroj]) == 0:
                seznam_kola.append(zdroj)
        # presunout ze seznamu kola do výsledku
        seznam_vystup += seznam_kola
        # smazat ty co šli do výstupu
        for odstranit in seznam_kola:
            del slovnik_vstup[odstranit]
        # smazat názvy přesunuté z FK tabulek, již existují
        for presunuta in seznam_kola:
            for zdroj in slovnik_vstup:
                if presunuta in slovnik_vstup[zdroj]:
                    slovnik_vstup[zdroj].remove(presunuta)

        cislo_iterace += 1

    if cislo_iterace == max_pocet_iteraci:
        raise ValueError('Cyklický odkaz mezi tabulkami nemá řešení')

    vysledek = ','.join(seznam_vystup)
    print(f' Výsledek:{vysledek}')
    return vysledek


# serad_tabulky('t1,t2,t3', 't1-t2,t2-t3,t3-t1')
# serad_tabulky('t1,t2,t3', '')
# serad_tabulky('t1,t2,t3', 't1-t3')
