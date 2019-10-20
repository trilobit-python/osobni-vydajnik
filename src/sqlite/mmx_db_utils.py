# -*- coding: UTF-8 -*-
'''
Created on 28.12.2012

@author: root
'''
import locale
import os

from sqlalchemy.orm import class_mapper

from src.sqlite.sqlalchemy_declarative import ACCOUNTLISTV1, PAYEEV1, CATEGORYV1, SUBCATEGORYV1

locale.setlocale(locale.LC_ALL, "")


# --------------------------- pomocné DB funkce
def getACCOUNTID(session: object, accName: object) -> object:
    ret = session.query(ACCOUNTLISTV1.ACCOUNTID).filter(ACCOUNTLISTV1.ACCOUNTNAME == accName).scalar()
    return ret


def getPAYEEID(session, parName):
    ret = session.query(PAYEEV1.PAYEEID).filter(PAYEEV1.PAYEENAME == parName).scalar()
    return ret


def getCATEGID(session, parName):
    ret = session.query(CATEGORYV1.CATEGID).filter(CATEGORYV1.CATEGNAME == parName).scalar()
    return ret


def getSUBCATEGID(session, parName):
    ret = session.query(SUBCATEGORYV1.SUBCATEGID).filter(SUBCATEGORYV1.SUBCATEGNAME == parName).scalar()
    return ret


def get_win_abs_path(argPath):
    if os.path.isabs(argPath):
        return argPath
    else:
        return os.path.abspath(argPath)


def asdict(obj):
    return dict((col.name, getattr(obj, col.name))
                for col in class_mapper(obj.__class__).mapped_table.c)
