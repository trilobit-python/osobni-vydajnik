# Příliš žluťoučký kůň úpěl ďábelské ódy.
"""
Načte zadaný soubor a spustí každý řádek jako příkaz,
pokud nastane chyba tak skončí(lze změnit parametrem)
"""

import argparse
import pathlib
import subprocess
import textwrap


def spust(prikaz: str, ignore_errors: bool):
    print(f'EXEC:{prikaz}', end='')
    try:
        proc = subprocess.Popen(prikaz, encoding='windows-1250', shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if err == '':
            print(f'\n{textwrap.indent(out, " OUT:")}')
        else:
            print(f'\n{textwrap.indent(err, " ERR:")}')
            if not ignore_errors:
                raise ValueError(f'Konec zpracován - chyba při spuštění skriptu chyba\n{err}')
    except subprocess.CalledProcessError as e:
        print(e.output)
        if not ignore_errors:
            raise ValueError(f'Konec zpracován - chyba při spuštění skriptu chyba\n{e.output}')


def spust_prikazy(soubor: str, ignore_errors: bool):
    if not pathlib.Path(soubor).is_file():
        raise ValueError(f'Neexistuje soubor: {soubor}')

    print(f'Načítám ze souboru: {soubor}')
    with open(soubor, encoding='windows-1250') as f:
        for radek in f.read().splitlines():
            spust(radek, ignore_errors)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=textwrap.dedent('''\
            Načte zadaný soubor a spustí každý řádek jako příkaz,
              pokud nastane u některého chyba - tak skončí (lze změnit parametrem)'''),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("soubor_s_prikazy", help="Název souboru s řádky jako příkazy")
    parser.add_argument("--ignore-errors", action="store_true", help="Neskončí na první chybě")
    args = parser.parse_args()

    spust_prikazy(args.soubor_s_prikazy, args.ignore_errors)
