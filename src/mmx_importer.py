# Příliš žluťoučký kůň úpěl ďábelské ódy.
# -------------------------------------------------------------------------------
# Name:        importer transakcni historie do sqlite DB souboru aplikace MME MoneyManagerEx
# Author:      David Němec
# Created:     3.12.2023                           původní první verze 11/01/2016
# -------------------------------------------------------------------------------
import os
import pathlib
import sys
from pathlib import Path

import click
import pandas as pd
import sqlalchemy
from click import echo
from sqlalchemy import text


# Class of different styles
class Style:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


DESCRIPTION = 'Import výpisů z bank do programu MoneyManagerEx'


@click.command('mmx_importer', help=DESCRIPTION)
@click.argument('mmx_file', type=click.Path(exists=True, file_okay=True, readable=True))
@click.argument('trans_hist_dir', type=click.Path(exists=True, file_okay=False, readable=True, path_type=Path))
def main(mmx_file, trans_hist_dir):
    # aktuální cestu do cesty python knihoven
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

    echo(DESCRIPTION)
    echo('')
    echo(f'MMX_FILE: {mmx_file}')
    echo(f'TRANS_HIST_DIR: {trans_hist_dir}')
    echo('')

    # otevření sqlite databáze z cesty
    engine = sqlalchemy.create_engine(f'sqlite:///{mmx_file}')
    engine.connect()

    # získání všech definic pro import z tabulky VYD_UCET_BANKA sloupce
    df_ucty = pd.read_sql(con=engine, sql=text("""
        select av.ACCOUNTID, av.ACCOUNTNAME, av.importer_trida, av.vypis_adresar, av.vypis_nazev_maska
        from ACCOUNTLIST_V1 av
        where av.importer_trida is NOT NULL
        and av.vypis_adresar is not NULL
        and av.vypis_nazev_maska is not NULL
        order by av.ACCOUNTID"""))
    # echo(df.to_string())

    for ucet in df_ucty.itertuples(name='účet'):
        echo(f'** Importuji výpisy {ucet.ACCOUNTNAME}', nl=False)
        echo(f' ({ucet.importer_trida}/{ucet.vypis_adresar}/{ucet.vypis_nazev_maska})')

        # vyhledání souborů k importu
        p = pathlib.Path.joinpath(trans_hist_dir, ucet.vypis_adresar)
        for i in p.glob(ucet.vypis_nazev_maska):
            csv_cela_cesta = (p / i)
            echo('   ' + str(csv_cela_cesta))

            if ucet.importer_trida == 'AirBankImporter':

                # načteme vše jako řetězce pak nastavíme správné typy
                rows = pd.read_csv(csv_cela_cesta, delimiter=';', encoding='cp1250', keep_default_na=False, dtype=str)
                datumy = ['Datum provedení', # 'Datum a čas zadání',
                          'Datum splatnosti', 'Datum schválení', 'Datum zaúčtování']
                # rows[datumy] = pd.to_datetime(rows[datumy], format='%d/%m/%Y')
                # rows[datumy] = pd.to_datetime(rows[datumy])
                rows[datumy] = rows[datumy].apply(
                    lambda x: pd.to_datetime(x, errors='coerce', format='%d/%m/%Y', utc=False).dt.date)
                print(rows.applymap(type).to_string())



            else:
                raise ValueError(f'Nenámá třída({ucet.importer_trida}) nelze provést import.')

            rows['ACCOUNTID'] = ucet.ACCOUNTID
            rows.to_sql(ucet.importer_trida, con=engine, if_exists='replace')
            print(rows)

        echo('')

    echo(f'Vše hotovo')


if __name__ == '__main__':
    os.system("")
    main()
