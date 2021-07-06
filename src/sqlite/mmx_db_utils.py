# -*- coding: UTF-8 -*-
"""
Created on 28.12.2012

@author: root
"""
import locale
import os
import sqlite3

from sqlalchemy.orm import class_mapper

locale.setlocale(locale.LC_ALL, "")


def get_scalar_result(cursor, sql, params=None):
    cursor.execute(sql, params)
    sqlite3.enable_callback_tracebacks(True)
    val = cursor.fetchone()
    sqlite3.enable_callback_tracebacks(False)
    if val:
        return val[0]
    return None


# --------------------------- pomocné DB funkce
def getACCOUNTID(cursor, accName: str):
    # ret = session.query(ACCOUNTLISTV1.ACCOUNTID).filter(ACCOUNTLISTV1.ACCOUNTNAME == accName).scalar()
    return get_scalar_result(cursor,
                             "select ACCOUNTID from ACCOUNTLIST_V1 where ACCOUNTNAME = :name ",
                             {'name': accName})


def get_win_abs_path(argPath):
    if os.path.isabs(argPath):
        return argPath
    else:
        return os.path.abspath(argPath)


def asdict(obj):
    return dict((col.name, getattr(obj, col.name))
                for col in class_mapper(obj.__class__).mapped_table.c)
