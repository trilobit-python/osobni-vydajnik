#
# Hádání čísel metodou půlení intervalu


import msvcrt

spodek = 1
vrsek = 100
pokusy = 0

print(f'Start mysli si celé číslo od {spodek} do {vrsek}')

while spodek != vrsek:
    x_nove = int((spodek + vrsek) / 2)
    print('Je větší než > ' + str(x_nove))
    c = msvcrt.getch().decode('ascii').upper()
    print(' Odpověděl ', c)
    if c == 'A':
        spodek = x_nove + 1
        pokusy = pokusy + 1
    elif c == 'N':
        vrsek = x_nove
        pokusy = pokusy + 1
    else:
        print('Tiskni jen písmena A nebo N')

print(f'Bylo to číslo:{str(spodek)}?    Uhádnuto v {pokusy}. pokusu')
