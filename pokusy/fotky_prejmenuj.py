#!/usr/bin/env python3
# -*- coding: windows-1250 -*-
#
# popis text u parametrů
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

# seznam podporovaných přípon
PODPOROVANE_PRIPONY = ['jpg', 'mts', 'avi', 'mp4', 'mov']

# konstanty pro statistiku
ZKONTROLOVANO = 'Zkontrolovano'
NELZE_URCIT = 'Nelze určit'
V_PORADU = 'V pořádku'
PREJMENOVANO = 'Opraveno'
NA_PREJMENOVANI = 'Na přejmenování'
PODEZRELE_DATUM = 'Podezřelé datum'

nazvy_poli_statistiky = [ZKONTROLOVANO, V_PORADU, NA_PREJMENOVANI, PREJMENOVANO, NELZE_URCIT, PODEZRELE_DATUM]

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


def zpracuj_soubor(p_root, p_fname, celkova_statistika, p_priznaky_nastaveni_programu):
    full_path = os.path.join(p_root, p_fname)
    name, extension = os.path.splitext(os.path.basename(full_path))
    celkova_statistika.update([ZKONTROLOVANO])

    cas_vzniku_z_nazvu = datum_vzniku_z_nazvu(full_path)
    cas_vzniku_z_metadat = datum_vytvoreni_z_metadat(full_path)

    vytvoreno, zmeneno, otevreno = get_file_time_info(full_path)
    cas_vzniku_ze_souboru = min(vytvoreno, zmeneno, otevreno)
    if vytvoreno > zmeneno:
        print(f'{full_path} Oprava vytvořeno ({popis_datetime_tz(vytvoreno)}) > změněno ({popis_datetime_tz(zmeneno)})')
        set_mtime(full_path, cas_vzniku_ze_souboru)
    try:
        novy_nazev_bez_pripony = doporuceny_nazev_souboru_bez_pripony(cas_vzniku_z_metadat, cas_vzniku_z_nazvu,
                                                                      cas_vzniku_ze_souboru)
    except Exception as err:
        print(f"ERROR {full_path}: {err}")
        celkova_statistika.update([PODEZRELE_DATUM])
        return

    if not novy_nazev_bez_pripony:
        raise ValueError(f'Nelze vytvožit nový název {p_fname}')

    novy_nazev = novy_nazev_bez_pripony + extension.lower()
    maska_s_precislovanim = f'{novy_nazev_bez_pripony}\\(\\d*\\){extension.lower()}'
    if novy_nazev == p_fname or re.match(maska_s_precislovanim, p_fname):
        celkova_statistika.update([V_PORADU])
        return

    s_info_radek = f'{p_fname}({novy_nazev}) {popis_datetime_tz(cas_vzniku_z_metadat)} ' \
                   f'{popis_datetime_tz(cas_vzniku_ze_souboru)} {popis_datetime_tz(cas_vzniku_z_nazvu)}'
    print(s_info_radek)
    celkova_statistika.update([NA_PREJMENOVANI])

    # pokud existuje v cíl soubor stejného jména přidá nejbližší volné číslo do názvu
    kam_cela_cesta_soubor_kam = os.path.join(p_root, novy_nazev)
    name, extension = os.path.splitext(os.path.basename(kam_cela_cesta_soubor_kam))
    i = 0
    while os.path.isfile(kam_cela_cesta_soubor_kam):  # rename if exists in same time
        i += 1
        kam_cela_cesta_soubor_kam = os.path.join(p_root, "%s(%d)%s" % (name, i, extension))

    if OPRAVDU_PREJMENUJ in p_priznaky_nastaveni_programu:
        print(f'Přejmenování {full_path} --> {kam_cela_cesta_soubor_kam}')
        os.rename(full_path, kam_cela_cesta_soubor_kam)
        celkova_statistika.update([PREJMENOVANO])


def main(p_dir, p_priznaky_nastaveni_programu):
    source_dir_name = os.path.abspath(p_dir)
    celkova_statistika = Counter()

    # sys.stdout.reconfigure(encoding='windows-1250')
    sys.stdout = Logger(source_dir_name)
    print(f'Kontrola/přejmenování souborů dle metadat (EXIF, MediaInfo, ...), a oprava datumu vytvoření')
    print(f'Kontroluji strom   : {source_dir_name}')
    print(f'Podporované přípony: {str(PODPOROVANE_PRIPONY)}')
    print(f'Příznaky nastavení : {str(p_priznaky_nastaveni_programu)}')

    for root, dirs, files in os.walk(source_dir_name, topdown=False):
        for fname in files:
            pripona = os.path.splitext(fname)[1].lower().replace('.', '')
            if pripona in PODPOROVANE_PRIPONY:
                zpracuj_soubor(root, fname, celkova_statistika, p_priznaky_nastaveni_programu)

    print(f'Celková statistika : {dict(celkova_statistika)}')
    print(f'Vše hotovo')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(f'''
            popis:
              přejmenuje soubory ve stromu dle metadat, případně času vzniku souboru
                kořen stromu je parametr "dir"
                pracuje pouze se soubory s příponami: {PODPOROVANE_PRIPONY}
                metadata pro JPG jsou v EXIF, pro MTS a MP4 jsou v hlavičce souboru
              pozor - opravdu přejmenuje až pokud je nastavena volba -write jinak pouze vypisuje 
                '''),
        formatter_class=RawTextHelpFormatter)

    parser.add_argument('dir', help='kořenový adresář stromu pro přejmenování souborů', default='.')
    parser.add_argument('--write',
                        help='fyzicky pžejmenuje soubory, bez tohoto příznaku pouze vypisuje', action='store_true',
                        default=False)
    a = parser.parse_args()

    priznaky_nastaveni_programu = []
    if a.write:
        priznaky_nastaveni_programu.append(OPRAVDU_PREJMENUJ)

    print(a)

    main(a.dir, priznaky_nastaveni_programu)
