#!/usr/bin/env python3
# -*- coding: windows-1250 -*-
#
# popis text u parametrů
#
import argparse
import datetime
import os
import sys
import textwrap
from argparse import RawTextHelpFormatter
from collections import Counter
from os.path import join

from .ext_file_info import popis_datetime_tz, datum_vzniku_z_nazvu, ensure_dir

# seznam podporovaných přípon
PODPOROVANE_PRIPONY = ['jpg', 'mp4', 'mts', 'avi', 'mov']

# konstanty pro statistiku
ZKONTROLOVANO = 'Zkontrolovano'
V_PORADU = 'V pořádku'
PRESUNUTO = 'Přesunuto'
NA_PRESUN = 'Na přesun'

nazvy_poli_statistiky = [ZKONTROLOVANO, V_PORADU, NA_PRESUN, PRESUNUTO]

# konstanty pro nastavení funkčnosti programu
OPRAVDU_PREJMENUJ = 'write'


class Logger(object):
    def __init__(self, path=None):
        self.terminal = sys.stdout
        log_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        log_name = f"{os.path.splitext(os.path.basename(__file__))[0]}_{log_time_str}.log"
        if path:
            log_name = os.path.join(path, log_name)
        self.log = open(log_name, "a", encoding='windows-1250')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.log.flush()


def datetime_str(date: datetime):
    return date.strftime('%Y-%m-%d %H:%M:%S')


def nastav_pokud_uz_nema_hodnotu(vysledek: datetime, nova_hodnota: datetime):
    #
    if nova_hodnota and nova_hodnota.date() < datetime.date(1970, 1, 1):
        raise ValueError(f'Podezřelé datum {popis_datetime_tz(nova_hodnota)}')
    if vysledek:
        return vysledek
    return nova_hodnota


def doporuceny_nazev_souboru_bez_pripony(p_cas_vzniku_z_metadat: datetime,
                                         p_cas_vzniku_z_nazvu: datetime,
                                         p_cas_vzniku_souboru: datetime_str,
                                         p_format_nazvu: str = '%Y-%m-%d %H-%M-%S'):
    """vrátí doporučený název souboru ve tvaru dle parametru p_format_nazvu
    postupně se snaží najít datum, který použije

    """
    datum = None
    datum = nastav_pokud_uz_nema_hodnotu(datum, p_cas_vzniku_z_metadat)
    datum = nastav_pokud_uz_nema_hodnotu(datum, p_cas_vzniku_z_nazvu)
    datum = nastav_pokud_uz_nema_hodnotu(datum, p_cas_vzniku_souboru)

    if datum:
        return f'{datum.strftime(p_format_nazvu)}'
    return None


def zpracuj_soubor(p_root, p_fname, celkova_statistika, p_priznaky_nastaveni_programu, p_cil_koren):
    full_path = os.path.join(p_root, p_fname)
    # print(full_path)
    name, extension = os.path.splitext(os.path.basename(full_path))
    celkova_statistika.update([ZKONTROLOVANO])

    cas_vzniku_z_nazvu = datum_vzniku_z_nazvu(full_path)
    cela_cesta_novy_adresar = join(p_cil_koren, cas_vzniku_z_nazvu.strftime("%Y"))
    cela_cesta_novy_adresar = join(cela_cesta_novy_adresar, cas_vzniku_z_nazvu.strftime("%m"))

    if cela_cesta_novy_adresar == p_root:
        celkova_statistika.update([V_PORADU])
        return

    novy_nazev_bez_pripony = doporuceny_nazev_souboru_bez_pripony(cas_vzniku_z_nazvu, cas_vzniku_z_nazvu,
                                                                  cas_vzniku_z_nazvu)
    novy_nazev = novy_nazev_bez_pripony + extension.lower()

    kam_cela_cesta_soubor_kam = os.path.join(cela_cesta_novy_adresar, novy_nazev)
    name, extension = os.path.splitext(os.path.basename(kam_cela_cesta_soubor_kam))
    i = 0
    while os.path.isfile(kam_cela_cesta_soubor_kam):  # rename if exists in same time
        i += 1
        kam_cela_cesta_soubor_kam = os.path.join(cela_cesta_novy_adresar, "%s(%d)%s" % (name, i, extension))

    if OPRAVDU_PREJMENUJ in p_priznaky_nastaveni_programu:
        # opravdu fyzicky přesune
        print(f'Přesun {full_path} --> {kam_cela_cesta_soubor_kam}', end='')
        ensure_dir(cela_cesta_novy_adresar)
        os.rename(full_path, kam_cela_cesta_soubor_kam)
        celkova_statistika.update([PRESUNUTO])
        print(' OK')
    else:
        # pouze vypíše kontrolu
        s_info_radek = f'{full_path} -> {kam_cela_cesta_soubor_kam}'
        print(s_info_radek)
        celkova_statistika.update([NA_PRESUN])


def main(p_dir, p_cil_koren, p_priznaky_nastaveni_programu):
    source_dir_name = os.path.abspath(p_dir)
    celkova_statistika = Counter()

    sys.stdout = Logger(source_dir_name)
    print(f'Kontrola/přesun  souborů dle jejich názvu ve tvaru ')
    print(f'Kontroluji strom   : {source_dir_name}')
    print(f'Podporované přípony: {str(PODPOROVANE_PRIPONY)}')
    print(f'Příznaky nastavení : {str(p_priznaky_nastaveni_programu)}')
    print(f'Kontroluji strom   : {source_dir_name}')
    print(f'Cílový strom       : {p_cil_koren}')

    for root, dirs, files in os.walk(source_dir_name, topdown=False):
        for fname in files:
            pripona = os.path.splitext(fname)[1].lower().replace('.', '')
            if pripona in PODPOROVANE_PRIPONY:
                zpracuj_soubor(root, fname, celkova_statistika, p_priznaky_nastaveni_programu, p_cil_koren)

    print(f'Celková statistika : {dict(celkova_statistika)}')
    print(f'Vše hotovo')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(r'''
            popis:
              dle názvu souboru přesune fotky do adresáře cil_koren\ROK\MESIC

                kořen stromu je parametr "dir"
                pracuje pouze se soubory s příponami: {PODPOROVANE_PRIPONY}
                metadata pro JPG jsou v EXIF, pro MTS a MP4 jsou v hlavičce souboru
              pozor - opravdu přejmenuje až pokud je nastavena volba -write jinak pouze vypisuje 
                '''),
        formatter_class=RawTextHelpFormatter)

    parser.add_argument('dir', help='kořenový adresář stromu pro přejmenování souborů', default='.')
    parser.add_argument('cil_koren', help='kořenový adresář stromu kam se bude přesouvat')
    parser.add_argument('--write',
                        help='fyzicky přesune soubory, bez tohoto příznaku pouze vypisuje', action='store_true',
                        default=False)
    a = parser.parse_args()

    priznaky_nastaveni_programu = []
    if a.write:
        priznaky_nastaveni_programu.append(OPRAVDU_PREJMENUJ)

    print(a)

    main(a.dir, a.cil_koren, priznaky_nastaveni_programu)
