#!/usr/bin/env python3
# -*- coding: windows-1250 -*-
#
# popis text u parametr�
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

# seznam podporovan�ch p��pon
PODPOROVANE_PRIPONY = ['jpg', 'mp4', 'mts', 'avi', 'mov']

# konstanty pro statistiku
ZKONTROLOVANO = 'Zkontrolovano'
V_PORADU = 'V po��dku'
PRESUNUTO = 'P�esunuto'
NA_PRESUN = 'Na p�esun'

nazvy_poli_statistiky = [ZKONTROLOVANO, V_PORADU, NA_PRESUN, PRESUNUTO]

# konstanty pro nastaven� funk�nosti programu
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
        raise ValueError(f'Podez�el� datum {popis_datetime_tz(nova_hodnota)}')
    if vysledek:
        return vysledek
    return nova_hodnota


def doporuceny_nazev_souboru_bez_pripony(p_cas_vzniku_z_metadat: datetime,
                                         p_cas_vzniku_z_nazvu: datetime,
                                         p_cas_vzniku_souboru: datetime_str,
                                         p_format_nazvu: str = '%Y-%m-%d %H-%M-%S'):
    """vr�t� doporu�en� n�zev souboru ve tvaru dle parametru p_format_nazvu
    postupn� se sna�� naj�t datum, kter� pou�ije

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
        # opravdu fyzicky p�esune
        print(f'P�esun {full_path} --> {kam_cela_cesta_soubor_kam}', end='')
        ensure_dir(cela_cesta_novy_adresar)
        os.rename(full_path, kam_cela_cesta_soubor_kam)
        celkova_statistika.update([PRESUNUTO])
        print(' OK')
    else:
        # pouze vyp�e kontrolu
        s_info_radek = f'{full_path} -> {kam_cela_cesta_soubor_kam}'
        print(s_info_radek)
        celkova_statistika.update([NA_PRESUN])


def main(p_dir, p_cil_koren, p_priznaky_nastaveni_programu):
    source_dir_name = os.path.abspath(p_dir)
    celkova_statistika = Counter()

    sys.stdout = Logger(source_dir_name)
    print(f'Kontrola/p�esun  soubor� dle jejich n�zvu ve tvaru ')
    print(f'Kontroluji strom   : {source_dir_name}')
    print(f'Podporovan� p��pony: {str(PODPOROVANE_PRIPONY)}')
    print(f'P��znaky nastaven� : {str(p_priznaky_nastaveni_programu)}')
    print(f'Kontroluji strom   : {source_dir_name}')
    print(f'C�lov� strom       : {p_cil_koren}')

    for root, dirs, files in os.walk(source_dir_name, topdown=False):
        for fname in files:
            pripona = os.path.splitext(fname)[1].lower().replace('.', '')
            if pripona in PODPOROVANE_PRIPONY:
                zpracuj_soubor(root, fname, celkova_statistika, p_priznaky_nastaveni_programu, p_cil_koren)

    print(f'Celkov� statistika : {dict(celkova_statistika)}')
    print(f'V�e hotovo')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(r'''
            popis:
              dle n�zvu souboru p�esune fotky do adres��e cil_koren\ROK\MESIC

                ko�en stromu je parametr "dir"
                pracuje pouze se soubory s p��ponami: {PODPOROVANE_PRIPONY}
                metadata pro JPG jsou v EXIF, pro MTS a MP4 jsou v hlavi�ce souboru
              pozor - opravdu p�ejmenuje a� pokud je nastavena volba -write jinak pouze vypisuje 
                '''),
        formatter_class=RawTextHelpFormatter)

    parser.add_argument('dir', help='ko�enov� adres�� stromu pro p�ejmenov�n� soubor�', default='.')
    parser.add_argument('cil_koren', help='ko�enov� adres�� stromu kam se bude p�esouvat')
    parser.add_argument('--write',
                        help='fyzicky p�esune soubory, bez tohoto p��znaku pouze vypisuje', action='store_true',
                        default=False)
    a = parser.parse_args()

    priznaky_nastaveni_programu = []
    if a.write:
        priznaky_nastaveni_programu.append(OPRAVDU_PREJMENUJ)

    print(a)

    main(a.dir, a.cil_koren, priznaky_nastaveni_programu)
