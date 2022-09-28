# -*- coding: UTF-8 -*-
"""
Created on 28.12.2012

@author: root
"""
import os
import re

from pandas import DataFrame
from pandas import option_context


def value_by_index(keys, values, item_name):
    ret_value = ""
    if item_name in keys:
        n_index = keys.index(item_name)
        if len(values) >= n_index:
            ret_value = values[n_index]
    return ret_value


def quoted_str(string):
    return '"' + string + '"'


def quoted_str_and_comma(string):
    return '"' + string + '",'


def remove_rep_spaces(s):
    return re.sub('[ \t]+', ' ', s)


class Reg(object):
    def __init__(self, cursor, row):
        for (attr, val) in zip((d[0] for d in cursor.description), row):
            setattr(self, attr, val)


def get_win_abs_path(path):
    if os.path.isabs(path):
        return path
    else:
        return os.path.abspath(path)


def print_frame(df: DataFrame, title: str = None, data_prefix: str = ''):
    if title:
        print(title)

    with option_context('expand_frame_repr', False, 'display.max_colwidth', None):
        for line in df.to_string().split('\n'):
            print(f'{data_prefix}{line}')


def spoj_seznam_retezcu(seznam_retezcu_list=[], oddelovac: str = ':', odstran_zdvojene_mezery: bool = True):
    seznam = filter(lambda name: name.strip(), seznam_retezcu)
    seznam = filter(lambda name: name != "\'\'", seznam)
    vysledek = ':'.join(filter(None, seznam))
    if odstran_zdvojene_mezery:  # remove duplicate spaces
        vysledek = " ".join(re.split("\s+", vysledek, flags=re.UNICODE))
    return vysledek
