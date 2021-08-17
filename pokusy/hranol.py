import math


def hranol(a, b, v):
    c = math.sqrt(a * a + b * b)
    print(f'a:{a} X b:{b} c:{c}')
    Sp = a * b / 2
    Spl = v * (a + b + c)
    S = 2 * Sp + Spl
    V = Sp * v
    print('Sp:', Sp)
    print('Spl:', Spl)
    print('S:', S)
    print(f'{V}=')


hranol(30, 40, 200)
