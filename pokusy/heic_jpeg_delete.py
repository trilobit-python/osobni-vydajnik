#!/usr/bin/env python3
# -*- coding: windows-1250 -*-
#
# popis text u parametrů
#
import datetime
import os
import sys
import textwrap

import click

DESCRIPTION = textwrap.dedent(f'''
            popis:
              Odstraní všechny JPG soubory, pokud k nim existuje HEIC soubor stejného jména ve stejném adresáři'
              
              pozor - opravdu smaže JPG soubory pouze pokud je nastavena volba -v jinak pouze vypisuje 
                ''')

# konstanty pro statistiku
ZKONTROLOVANO = 'Zkontrolovano'
DUPLICITA = 'Duplicita'

nazvy_poli_statistiky = [ZKONTROLOVANO, DUPLICITA]

# konstanty pro nastavení funkčnosti programu
OPRAVDU_PREJMENUJ = 'vymaz'


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


@click.command()
@click.argument('vstup_adresar')
@click.option('--vymaz/--bez-vymazu', default=False)
def main(vstup_adresar, vymaz):
    f"""{DESCRIPTION}
      kořenový adresář stromu pro kontrolu
      vymaz/--bez-vymazu TODO popis 
            
    """

    source_dir_name = os.path.abspath(vstup_adresar)

    sys.stdout = Logger(source_dir_name)
    print(f'Odstraní všechny JPG soubory, pokud k nim existuje HEIC soubor stejného jména')
    print(f'Kontroluji strom   : {source_dir_name}')
    print(f'Vymazat JPG        : {str(vymaz)}')

    n_duplicity = 0
    n_vymazano = 0
    for root, dirs, files in os.walk(source_dir_name, topdown=False):
        for fname in files:
            pripona = os.path.splitext(fname)[1].lower().replace('.', '')
            if pripona == 'heic':
                # pokud exituje JPG stejneho jména
                full_path = os.path.join(root, fname)
                full_path_jpg = full_path.replace('.heic', '.jpg')
                if os.path.isfile(full_path_jpg):
                    n_duplicity += 1
                    print(full_path)
                    print(full_path_jpg)

                    if vymaz:
                        n_vymazano += 1
                        os.remove(full_path_jpg)
                        print(f'{full_path_jpg} byl smazán')

    print(f'Vše hotovo, nalezeno duplicit:{n_duplicity} vymazano:{n_vymazano}')


if __name__ == '__main__':
    main()
