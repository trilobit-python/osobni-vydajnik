# -*- coding: UTF-8 -*-
"""
Created on 28.12.2012

@author: root
"""
import os
import re


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


def print_frame(pandas, rows):
    pandas.set_option('expand_frame_repr', False)
    print(rows)
