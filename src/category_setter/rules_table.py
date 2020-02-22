#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
# Name:        nastavi kategorie a transfery v sqlite DB souboru aplikace MME MoneyManagerEx
# -------------------------------------------------------------------------------
import csv
import sys
import pandas
import os

# fname = r'c:\Users\root\PycharmProjects\osobni-vydajnik\src\category_setter\rules.csv'
fname =  os.path.join(os.path.abspath(os.path.dirname('.')), r'category_setter\rules.csv')
rows = pandas.read_csv(fname, delimiter=chr(9),
                       encoding='cp1250',
                       quoting=csv.QUOTE_NONE
                       )

rulePatternCatSubcat = {}  # pattern, categname:subcatname

for i, row in rows.iterrows():
    pattern = row['pattern']
    categ_sub = row['categname:subcatname']
    if pattern in rulePatternCatSubcat:
        print(f"Duplicitní definice pravidla:{pattern}")
        sys.exit(-1)
    else:
        rulePatternCatSubcat[pattern] = categ_sub

print(f'Načteno {len(rulePatternCatSubcat)} pravidel ze souboru {fname}')
