#!/usr/bin/env python3
# -*- coding: windows-1250 -*-
#
# popis text u parametr�
#
import argparse
import datetime
import os
import re
import sys
import textwrap
from argparse import RawTextHelpFormatter
from collections import Counter

from .ext_file_info import datum_vytvoreni_z_metadat, popis_datetime_tz, datum_vzniku_z_nazvu, \
    get_file_time_info, set_mtime

# seznam podporovan�ch p��pon
PODPOROVANE_PRIPONY = ['jpg', 'mts', 'avi', 'mp4', 'mov']

# konstanty pro statistiku
ZKONTROLOVANO = 'Zkontrolovano'
NELZE_URCIT = 'Nelze ur�it'
V_PORADU = 'V po��dku'
PREJMENOVANO = 'Opraveno'
NA_PREJMENOVANI = 'Na p�ejmenov�n�'
PODEZRELE_DATUM = 'Podez�el� datum'

nazvy_poli_statistiky = [ZKONTROLOVANO, V_PORADU, NA_PREJMENOVANI, PREJMENOVANO, NELZE_URCIT, PODEZRELE_DATUM]

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


def zpracuj_soubor(p_root, p_fname, celkova_statistika, p_priznaky_nastaveni_programu):
    full_path = os.path.join(p_root, p_fname)
    name, extension = os.path.splitext(os.path.basename(full_path))
    celkova_statistika.update([ZKONTROLOVANO])

    cas_vzniku_z_nazvu = datum_vzniku_z_nazvu(full_path)
    cas_vzniku_z_metadat = datum_vytvoreni_z_metadat(full_path)

    vytvoreno, zmeneno, otevreno = get_file_time_info(full_path)
    cas_vzniku_ze_souboru = min(vytvoreno, zmeneno, otevreno)
    if vytvoreno > zmeneno:
        print(f'{full_path} Oprava vytvo�eno ({popis_datetime_tz(vytvoreno)}) > zm�n�no ({popis_datetime_tz(zmeneno)})')
        set_mtime(full_path, cas_vzniku_ze_souboru)
    try:
        novy_nazev_bez_pripony = doporuceny_nazev_souboru_bez_pripony(cas_vzniku_z_metadat, cas_vzniku_z_nazvu,
                                                                      cas_vzniku_ze_souboru)
    except Exception as err:
        print(f"ERROR {full_path}: {err}")
        celkova_statistika.update([PODEZRELE_DATUM])
        return

    if not novy_nazev_bez_pripony:
        raise ValueError(f'Nelze vytvo�it nov� n�zev {p_fname}')

    novy_nazev = novy_nazev_bez_pripony + extension.lower()
    maska_s_precislovanim = f'{novy_nazev_bez_pripony}\\(\\d*\\){extension.lower()}'
    if novy_nazev == p_fname or re.match(maska_s_precislovanim, p_fname):
        celkova_statistika.update([V_PORADU])
        return

    s_info_radek = f'{p_fname}({novy_nazev}) {popis_datetime_tz(cas_vzniku_z_metadat)} ' \
                   f'{popis_datetime_tz(cas_vzniku_ze_souboru)} {popis_datetime_tz(cas_vzniku_z_nazvu)}'
    print(s_info_radek)
    celkova_statistika.update([NA_PREJMENOVANI])

    # pokud existuje v c�l soubor stejn�ho jm�na p�id� nejbli��� voln� ��slo do n�zvu
    kam_cela_cesta_soubor_kam = os.path.join(p_root, novy_nazev)
    name, extension = os.path.splitext(os.path.basename(kam_cela_cesta_soubor_kam))
    i = 0
    while os.path.isfile(kam_cela_cesta_soubor_kam):  # rename if exists in same time
        i += 1
        kam_cela_cesta_soubor_kam = os.path.join(p_root, "%s(%d)%s" % (name, i, extension))

    if OPRAVDU_PREJMENUJ in p_priznaky_nastaveni_programu:
        print(f'P�ejmenov�n� {full_path} --> {kam_cela_cesta_soubor_kam}')
        os.rename(full_path, kam_cela_cesta_soubor_kam)
        celkova_statistika.update([PREJMENOVANO])


def main(p_dir, p_priznaky_nastaveni_programu):
    source_dir_name = os.path.abspath(p_dir)
    celkova_statistika = Counter()

    # sys.stdout.reconfigure(encoding='windows-1250')
    sys.stdout = Logger(source_dir_name)
    print(f'Kontrola/p�ejmenov�n� soubor� dle metadat (EXIF, MediaInfo, ...), a oprava datumu vytvo�en�')
    print(f'Kontroluji strom   : {source_dir_name}')
    print(f'Podporovan� p��pony: {str(PODPOROVANE_PRIPONY)}')
    print(f'P��znaky nastaven� : {str(p_priznaky_nastaveni_programu)}')

    for root, dirs, files in os.walk(source_dir_name, topdown=False):
        for fname in files:
            pripona = os.path.splitext(fname)[1].lower().replace('.', '')
            if pripona in PODPOROVANE_PRIPONY:
                zpracuj_soubor(root, fname, celkova_statistika, p_priznaky_nastaveni_programu)

    print(f'Celkov� statistika : {dict(celkova_statistika)}')
    print(f'V�e hotovo')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(f'''
            popis:
              p�ejmenuje soubory ve stromu dle metadat, p��padn� �asu vzniku souboru
                ko�en stromu je parametr "dir"
                pracuje pouze se soubory s p��ponami: {PODPOROVANE_PRIPONY}
                metadata pro JPG jsou v EXIF, pro MTS a MP4 jsou v hlavi�ce souboru
              pozor - opravdu p�ejmenuje a� pokud je nastavena volba -write jinak pouze vypisuje 
                '''),
        formatter_class=RawTextHelpFormatter)

    parser.add_argument('dir', help='ko�enov� adres�� stromu pro p�ejmenov�n� soubor�', default='.')
    parser.add_argument('--write',
                        help='fyzicky p�ejmenuje soubory, bez tohoto p��znaku pouze vypisuje', action='store_true',
                        default=False)
    a = parser.parse_args()

    priznaky_nastaveni_programu = []
    if a.write:
        priznaky_nastaveni_programu.append(OPRAVDU_PREJMENUJ)

    print(a)

    main(a.dir, priznaky_nastaveni_programu)
