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


def pretypovani_sloupcu(df: pd.DataFrame, dny: str, casy: str, castky: str, fmt_dny: str = '%d/%m/%Y',
                        fmt_cas: str = '%d/%m/%Y %H:%M:%S', fmt_castky: str = '%n'):
    seznam_datum = dny.split(',')
    df[seznam_datum] = df[seznam_datum].apply(lambda x: pd.to_datetime(x, format=fmt_dny, utc=False).dt.date)
    seznam_cas = casy.split(',')
    df[seznam_cas] = df[seznam_cas].apply(lambda x: pd.to_datetime(x, format=fmt_cas, utc=False).dt.date)
    seznam_castka = castky.split(',')
    # df.a = df.a.astype(float).fillna(0.0)
    df[seznam_castka] = df[seznam_castka].replace(regex={',': '.'}).astype(float).fillna(0.0)
    # print(df.dtypes)


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

    for ucet in df_ucty.itertuples(name='účet'):
        echo(f'** Importuji výpisy {ucet.ACCOUNTNAME}', nl=False)
        echo(f' ({ucet.importer_trida}/{ucet.vypis_adresar}/{ucet.vypis_nazev_maska})')

        # vyhledání souborů k importu
        p = pathlib.Path.joinpath(trans_hist_dir, ucet.vypis_adresar)
        for i in p.glob(ucet.vypis_nazev_maska):
            csv_cela_cesta = (p / i)
            echo('   ' + str(csv_cela_cesta))

            from hashlib import md5
            from mmap import mmap, ACCESS_READ

            with open(csv_cela_cesta) as file, mmap(file.fileno(), 0, access=ACCESS_READ) as file:
                print(f'{csv_cela_cesta}:{md5(file).hexdigest()}')

            # načteme vše jako řetězce pak nastavíme správné typy
            col_names = pd.read_csv(csv_cela_cesta, nrows=0, encoding='cp1250', delimiter=';').columns
            types_dict = {}
            types_dict.update({col: str for col in col_names if col not in types_dict})
            rows = pd.read_csv(csv_cela_cesta, dtype=types_dict, encoding='cp1250', delimiter=';')

            if ucet.importer_trida == 'AirBankImporter':
                # 'Směr úhrady', 'Typ úhrady', ' Kategorie plateb', ' Měna účtu', ' Částka v měně účtu',
                # 'Poplatek v měně účtu', ' Původní měna úhrady', ' Původní částka úhrady', ' Název protistrany',
                # 'Číslo účtu protistrany', ' Název účtu protistrany', ' Variabilní symbol', ' Konstantní symbol',
                # 'Specifický symbol', ' Zdrojová obálka', ' Cílová obálka', ' Poznámka pro mne',
                # 'Zpráva pro příjemce', ' Poznámka k úhradě', ' Název karty', ' Číslo karty', ' Držitel karty',
                # 'Název zařízení', ' Obchodní místo', ' Směnný kurz', ' Odesílatel poslal', ' Poplatky jiných bank',
                # 'Datum a čas zadání', ' Datum splatnosti', ' Datum schválení', ' Datum zaúčtování',
                # 'Referenční číslo', 'Způsob zadání', 'Zadal', ' Zaúčtováno', ' Pojmenování příkazu',
                # 'Název, adresa a stát protistrany', 'Název, adresa a stát banky protistrany', 'Typ poplatku',
                # 'Účel úhrady', 'Zvláštní pokyny k úhradě', 'Související úhrady', 'Další identifikace úhrady',
                # 'Způsob úhrady'

                datumove_sloupce = 'Datum provedení,Datum splatnosti,Datum schválení,Datum zaúčtování'.split(',')
                datum_a_cas_sloupce = ['Datum a čas zadání']

                pretypovani_sloupcu(rows, dny='Datum provedení,Datum splatnosti,Datum schválení,Datum zaúčtování',
                                    casy='Datum a čas zadání',
                                    castky='Částka v měně účtu,Původní částka úhrady,Poplatek v měně účtu,'
                                         'Směnný kurz,Poplatky jiných bank')
                # print(rows.info)

            else:
                raise ValueError(f'Nenámá třída({ucet.importer_trida}) nelze provést import.')

            rows.insert(0, 'ACCOUNT', ucet.ACCOUNTID)
            rows.to_sql(ucet.importer_trida, con=engine, if_exists='replace')

        echo('')

    echo(f'Vše hotovo')


if __name__ == '__main__':
    os.system("")
    main()
