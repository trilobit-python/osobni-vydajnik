#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
# Name:        Generuje xlsx z Oracle schematu - popis tabulek
# Author:      P3402617
# Created:     16.10.2020
# Copyright:   NemecDa
# -------------------------------------------------------------------------------

import tkinter as tk

import openpyxl
import pandas as pd
from tkinter import filedialog

from xlsxwriter import Workbook

from src.utils.oracle_database import OracleDatabase


# root = tk.Tk()
# canvas1 = tk.Canvas(root, width=300, height=300, bg='lightsteelblue2', relief='raised')
# canvas1.pack()
def as_text(value):
    if value is None:
        return ""
    return str(value)


def oprav_sirku_sloupcu(ws):
    for column_cells in ws.columns:
        new_column_length = max(len(as_text(cell.value)) for cell in column_cells)
        new_column_letter = (openpyxl.utils.get_column_letter(column_cells[0].column))
        if new_column_length > 0:
            ws.column_dimensions[new_column_letter].width = new_column_length + 1


def get_col_widths(dataframe):
    # First we find the maximum length of the index column
    idx_max = max([len(str(s)) for s in dataframe.index.values] + [len(str(dataframe.index.name))])
    # Then, we concatenate this to the max of the lengths of column name and its values for each column, left to right
    return [idx_max] + [max([len(str(s)) for s in dataframe[col].values] + [len(col)]) for col in
                        dataframe.columns]


def exportExcel(p_vystup_xlsx):
    conn_str = 'oes_migr/oes_migr@oedev'
    db = OracleDatabase(conn_str)

    df = db.query('''
        select ut.TABLE_NAME, utc.COMMENTS, ut.TABLESPACE_NAME
          from user_tables ut
          join user_tab_comments utc
            on utc.TABLE_NAME = ut.TABLE_NAME
         where ut.TABLE_NAME like '%MIGRADO%'
         order by 1
    ''')

    writer = pd.ExcelWriter(p_vystup_xlsx, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Tabulky_Migrado', index=False)

    # pro každou tabulku vytvoř Sheet
    for table in df['TABLE_NAME']:
        print(table)
        df_table = db.query('''
            select utc.COLUMN_ID,
                   utc.COLUMN_NAME,
                   utc.DATA_TYPE,
                   utc.NULLABLE,
                   ucc.COMMENTS
              from user_tab_cols utc
              left join user_col_comments ucc
                on ucc.TABLE_NAME = utc.TABLE_NAME
               and ucc.COLUMN_NAME = utc.COLUMN_NAME
             where utc.TABLE_NAME = :table_name
             order by utc.COLUMN_ID
            ''', {'table_name': table})

        df_table.to_excel(writer, sheet_name=table, index=False)

        worksheet = writer.workbook().get_worksheet_by_name(table)
        for i, width in enumerate(get_col_widths(df_table)):
            worksheet.set_column(i, i, width)

    writer.save()


# saveAsButtonExcel = tk.Button(text='Export Excel', command=exportExcel, bg='green', fg='white',
#                               font=('helvetica', 12, 'bold'))
# canvas1.create_window(150, 150, window=saveAsButtonExcel)
#
# root.mainloop()

exportExcel(r'c:\tmp\DM_migrado.xlsx')
