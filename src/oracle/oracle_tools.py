#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
# Name:        Pomocne funkce pro migraci dat do Oracle
# Author:      P3402617
# Created:
# Copyright:   (c) P3402617
# -------------------------------------------------------------------------------
import cx_Oracle
import pandas as pd


def query(connection, p_query, p_params=None):
    df = pd.read_sql(p_query, connection, params=p_params)
    return df


def query_ret_rownum(connection, p_query, p_params=None):
    """execute query and return only number of rows in result"""
    df = query(connection, p_query, p_params)
    return len(df.index)



