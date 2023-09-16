#!/usr/bin/env python3
# -*- coding: windows-1250 -*-
#
# Rozšiřující funkce pro práci se soubory
#   - časy vytvoření načíst/nastavit (problém s časovou zónou systému,...)
#   - informace o multimediálních souborech metadata v hlavičce nebo těle dat
#
#   tj. soubory s příponoum (jpg|mp4|mts)
#   u každého souboru opraví atributy Čas vytvoření, Čas změny a Čas přístupu dle Metadat v souboru
#   metadata pro JPG jsou EXIF pro MTS a MP4 metadata v hlavičce souboru
#
import datetime
import os
import pathlib
import re

import mediameta as mm
import pytz
import pywintypes
import win32con
import win32file
from PIL import Image, ExifTags
from hachoir.core import config as hachoir_config
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pymediainfo import MediaInfo

hachoir_config.quiet = True

Praha_TZINFO = pytz.timezone(pytz.country_timezones('cz')[0])
UTC_TZINFO = pytz.utc


def ensure_dir(p_dir):
    pathlib.Path(p_dir).mkdir(parents=True, exist_ok=True)
    return p_dir


def popis_datetime_tz(datum_s_cas_zonou):
    if datum_s_cas_zonou:
        return datum_s_cas_zonou.strftime("%d.%m.%Y %H:%M:%S %Z")
    return '                 None'


def mp4_metadata_time(filename):
    mp4_parser = createParser(filename)
    if not mp4_parser:
        print("Unable to parse file %s" % filename)
    with mp4_parser:
        try:
            metadata = extractMetadata(mp4_parser)
        except Exception as err:
            print("Metadata extraction error: %s" % err)
            metadata = None
    if not metadata:
        print(f"Unable to extract metadata: {filename}")
    creation_str = metadata.getText('creation_date')

    if creation_str and creation_str != '1904-01-01 00:00:00':
        utc_time = datetime.datetime.strptime(creation_str, "%Y-%m-%d %H:%M:%S")
        utc_time = utc_time.replace(tzinfo=UTC_TZINFO)
        loc_time = utc_time.astimezone(Praha_TZINFO)
        return loc_time
    return None


def exif_date_time(filename):
    image = Image.open(filename)
    image.verify()
    exif = {
        ExifTags.TAGS[k]: v
        for k, v in image.getexif().items()
        if k in ExifTags.TAGS
    }

    str_cre_date_exif = None
    # hledáme první minímální čas
    for popis in ['DateTimeOriginal', 'DatetimeDigitized', 'DateTime']:
        # for popis in ['DateTime', 'DateTimeOriginal', 'DatetimeDigitized']:
        if popis in exif.keys():
            hodnota = exif[popis]
            if hodnota != '0000:00:00 00:00:00':
                if not str_cre_date_exif:
                    str_cre_date_exif = hodnota
                else:
                    str_cre_date_exif = min(hodnota, str_cre_date_exif)

    if str_cre_date_exif:
        if str_cre_date_exif[11:13] == '24':  # korekce pocet hodin > 24
            str_cre_date_exif = f'{str_cre_date_exif[:11]}00{str_cre_date_exif[13:]}'

        cre_date_exif = datetime.datetime.strptime(str_cre_date_exif, '%Y:%m:%d %H:%M:%S')
        return cre_date_exif.astimezone(Praha_TZINFO)
    return None


def datum_vzniku_z_nazvu(p_filename):
    """vrátí datum vzniku souboru vypočtený z názvu souboru v časové zóně Praha
    očekávané formáty názvu souboru:
       2012.01.15 14.29.21.jpg tj. maska
    """
    nazev, pripona = os.path.splitext(os.path.basename(p_filename))
    seznam_dvojic_maska_parse_fmt = [(r'(\d{4}-\d{2}-\d{2}\ \d{2}-\d{2}-\d{2}).*', '%Y-%m-%d %H-%M-%S'),
                                     (r'(\d{4}-\d{2}-\d{2}\ \d{2}\.\d{2}\.\d{2}).*', '%Y-%m-%d %H.%M.%S'),
                                     (r'(\d{4}-\d{2}-\d{2}\ \d{6}).*', '%Y-%m-%d %H%M%S'),
                                     (r'(\d{4}-\d{2}-\d{8}).*', '%Y-%m-%d%H%M%S'),
                                     (r'(\d{2}-\d{2}-\d{2}_\d{2}-\d{2})(\.00)', '%y-%m-%d_%H-%M')]
    for dvojice in seznam_dvojic_maska_parse_fmt:
        maska, parse_fmt = dvojice[0], dvojice[1]
        if re.match(maska, nazev):
            vyraz = re.sub(maska, r'\g<1>', nazev)
            vytvoreno = datetime.datetime.strptime(vyraz, parse_fmt)
            return vytvoreno.astimezone(Praha_TZINFO)
    return None


def datum_vytvoreni_z_metadat(full_path):
    extension = os.path.splitext(full_path)[1].lower().replace('.', '').lower()

    if extension in ['jpg']:
        datum_z_metadat = exif_date_time(full_path)
    elif extension in ['mts', 'avi', 'bmp']:
        datum_z_metadat = MOV_datum_vytvoreni_z_media(full_path)
    elif extension in ['mp4']:
        datum_z_metadat = mp4_metadata_time(full_path)
    elif extension in ['mov']:
        datum_z_metadat = MOV_datum_vytvoreni_z_media(full_path)
    elif extension in ['heic']:
        datum_z_metadat = HEIC_datum_vytvoreni_z_media(full_path)
    else:
        raise ValueError(f'Nelze určit datum vytvoření z metadat pro soubor: {full_path}')

    if datum_z_metadat:  # kontrola rozumnosti datumu - jinak None
        if datum_z_metadat < datetime.datetime(1970, 1, 1, 12, 0, 0, tzinfo=Praha_TZINFO):
            datum_z_metadat = None
    return datum_z_metadat


def HEIC_datum_vytvoreni_z_media(cela_cesta_k_souboru, pillow_heif=None):
    try:
        meta_data = mm.ImageMetadata(cela_cesta_k_souboru)
        str_recorded_date = meta_data['DateTimeOriginal']
        str_recorded_date += meta_data['OffsetTimeOriginal'].replace(':', '')  # konverze +02:00 na +0200

        if str_recorded_date:  # očekávaný řetězec: 2023:09:02 13:44:47+0200
            try:
                vytvoreno = datetime.datetime.strptime(str_recorded_date, '%Y:%m:%d %H:%M:%S%z')
                return vytvoreno.astimezone(Praha_TZINFO)
            except:
                raise ValueError(
                    f'Nelze určit datum z metadat pro: {cela_cesta_k_souboru} čas_str:{str_recorded_date}')
        else:
            return None

    except mm.UnsupportedMediaFile:
        raise ValueError(
            f'Nepodporovaný formát metadat pro: {cela_cesta_k_souboru}')


def MOV_datum_vytvoreni_z_media(cela_cesta_k_souboru):
    media_info = MediaInfo.parse(cela_cesta_k_souboru)
    str_recorded_date = None
    str_tag_name = None

    for track in media_info.general_tracks:
        for nazev in ['comapplequicktimecreationdate', 'recorded_date', 'mastered_date', 'tagged_date']:
            str_recorded_date = track.to_data().get(nazev, None)
            if str_recorded_date is not None:
                str_tag_name = nazev
                break

    if str_recorded_date:
        # Datumy příklady :UTC 2004-12-29 08:17:00.000, 2022-12-02T17:22:28+0100
        dvojice_maska_parse_fmt = [(r'^UTC\ (\d{4}-\d{2}-\d{2}\ \d{2}:\d{2}:\d{2})\.(\d{3})$', '%Y-%m-%d %H:%M:%S'),
                                   (r'^UTC\ (\d{4}-\d{2}-\d{2}\ \d{2}:\d{2}:\d{2})$', '%Y-%m-%d %H:%M:%S'),
                                   (r'^(\d{4}-\d{2}-\d{2}\ \d{2}:\d{2}:\d{2})\.(\d{3})$', '%Y-%m-%d %H:%M:%S'),
                                   (r'^(\d{4}-\d{2}-\d{2}\ \d{2}:\d{2}:\d{2}\+\d{2}:\d{2})$', '%Y-%m-%d %H:%M:%S%z'),
                                   (r'^(\d{4}-\d{2}-\d{2}\ \d{2}:\d{2}:\d{2})$', '%Y-%m-%d %H:%M:%S'),
                                   (r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{4})$', '%Y-%m-%dT%H:%M:%S%z')]
        for dvojice in dvojice_maska_parse_fmt:
            maska, parse_fmt = dvojice[0], dvojice[1]
            if re.match(maska, str_recorded_date):
                vyraz = re.sub(maska, r'\g<1>', str_recorded_date)
                vytvoreno = datetime.datetime.strptime(vyraz, parse_fmt)
                return vytvoreno.astimezone(Praha_TZINFO)
        raise ValueError(
            f'Nelze určit datum z metadat pro: {cela_cesta_k_souboru} čas_str:{str_recorded_date} tag:{str_tag_name}')
    else:
        return None


def timestamp_praha(p_timestamp):
    return Praha_TZINFO.localize(datetime.datetime.fromtimestamp(p_timestamp))


def get_file_time_info(p_full_file_path):
    """ vrací v datetime s TZ tyto časy: vytvořeno, změněno, otevřeno

    """
    stat = os.stat(p_full_file_path)
    return timestamp_praha(stat.st_ctime), timestamp_praha(stat.st_mtime), timestamp_praha(stat.st_atime)


def file_get_mtime(filename):
    dtm_tz = Praha_TZINFO.localize(datetime.datetime.fromtimestamp(os.path.getmtime(filename)))
    return dtm_tz


def set_mtime(p_fname, p_newtime):
    tstamp = p_newtime.timestamp()
    wintime = pywintypes.Time(tstamp)
    winfile = \
        win32file.CreateFile(p_fname, win32con.GENERIC_WRITE,
                             win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                             None, win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None)
    win32file.SetFileTime(winfile, wintime, wintime, wintime)
    winfile.close()


def presun_souboru_prip_docisluj(cesta_odkud, cesta_kam, nazev_souboru):
    if cesta_odkud != cesta_kam:
        kam_cela_cesta_soubor_odkud = os.path.join(cesta_odkud, nazev_souboru)
        kam_cela_cesta_soubor_kam = os.path.join(cesta_kam, nazev_souboru)
        name, extension = os.path.splitext(os.path.basename(kam_cela_cesta_soubor_kam))

        if not os.path.isdir(cesta_kam):
            print(f"Zakladam adresar:{cesta_kam}")
            os.makedirs(cesta_kam)

        # pokud existuje v cíl soubor stejného jména přidá nejbližší volné číslo do názvu
        i = 0
        while os.path.isfile(kam_cela_cesta_soubor_kam):  # rename if exists in same time
            i += 1
            kam_cela_cesta_soubor_kam = os.path.join(cesta_kam, "%s(%d)%s" % (name, i, extension))

        print(f'Přesun {kam_cela_cesta_soubor_odkud} --> {kam_cela_cesta_soubor_kam}')
        os.rename(kam_cela_cesta_soubor_odkud, kam_cela_cesta_soubor_kam)
