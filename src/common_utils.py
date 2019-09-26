# -*- coding: UTF-8 -*-
'''
Created on 28.12.2012

@author: root
'''
import fnmatch
import locale
import os
import re

from sqlalchemy.orm import class_mapper

from sqlalchemy_declarative import ACCOUNTLISTV1, PAYEEV1, CATEGORYV1, SUBCATEGORYV1

locale.setlocale(locale.LC_ALL, "")

def str_from_file(file_name):
    a_file = open(file_name, encoding='cp1250')
    out = a_file.read()
    a_file.close()
    return out

def str_to_file(string, file_name):
    a_file = open(file_name, encoding='cp1250', mode='w')
    a_file.write(string)
    a_file.close

def str_set_to_file(full_file_name, str_header, set_of_strings):
    # is result - write to file
    if len(set_of_strings)>0:
        a_file = open(full_file_name, encoding='cp1250', mode='w')
        if len(str_header)>0:
            a_file.write(str_header+'\n')
            ## pretriditimport locale
            sorted_list = sorted(set_of_strings)
            for line in sorted_list:
                a_file.write(line + "\n")
        print ("Write to file:" + full_file_name +" Number of lines:" + str(len(set_of_strings)))
        a_file.close()

def value_by_index(setKeys, setValues, itemName):
    retValue=""
    if itemName in setKeys:
        nIndex = setKeys.index(itemName)
        if len(setValues)>=nIndex:
            retValue = setValues[nIndex]
    return retValue

def quoted_str(string):
    return '"' + string + '"'

def quoted_str_and_comma(string):
    return '"' + string + '",'

def remove_rep_spaces(s):
    return re.sub('[ \t]+' , ' ', s)

class reg(object):
    def __init__(self, cursor, row):
        for (attr, val) in zip((d[0] for d in cursor.description), row):
            setattr(self, attr, val)


def find_files(dir_name, fmask):
    includes = [fmask] # for files only
    includes = r'|'.join([fnmatch.translate(x) for x in includes])
    ret_list = []
    for item in os.listdir(dir_name):
        if os.path.isfile(os.path.join(dir_name, item)):
            if re.match(includes, item):
                ret_list.append(os.path.join(dir_name, item))
    return ret_list


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


def print_DataFrame(pandas, rows):
    pandas.set_option('expand_frame_repr', False)
    print(rows)
