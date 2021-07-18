#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
""" Wrapper to call sqlite"""

import logging
import sqlite3
import sys
import traceback

import numpy as np
import pandas as pd


class SqliteDatabase(object):
    def __init__(self, sqlite_file_name):
        sqlite3.register_adapter(np.int64, lambda val: int(val))
        sqlite3.register_adapter(np.int32, lambda val: int(val))
        try:
            conn = sqlite3.connect(sqlite_file_name)
            self._db_connection = conn
            self._db_connection.set_trace_callback(print)
            self._cursor = self._db_connection.cursor()
        except sqlite3.Error as er:
            # raise ValueError(f'Failed to connect to database! {sqlite3.Error}')
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))
            raise ValueError(f'Failed to connect to database!')

    def __del__(self):
        if self._db_connection:
            self._db_connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def set_autocommit_off(self):
        self._db_connection.autocommit = False

    def set_autocommit_on(self):
        self._db_connection.autocommit = True

    def commit(self):
        """Commit a transaction"""
        return self._db_connection.commit()

    def rollback(self):
        """Roll-back a transaction"""
        return self._db_connection.rollback()

    def query(self, p_query, p_params=None):
        df = pd.read_sql(p_query, self._db_connection, params=p_params)
        return df

    def query_ret_rownum(self, p_query, p_params=None):
        """execute query and return only number of rows in result"""
        df = self.query(p_query, p_params)
        return len(df.index)

    def query_log_rownum(self, query, params=None, message=None):
        """  execute query
             log message and add number of rows
             return DataFrame with result
        """
        logging.debug(query)
        df = self.query(query, params)
        if message is None:
            logging.debug(f'rows returned:{len(df.index)}')
        else:
            logging.info(f'{message}:{len(df.index)}')
        return df

    def execute(self, sql, params=None):
        """Executes a raw query"""
        try:
            self._cursor.execute(sql, params)
        except Exception as e:
            raise e
        return self._cursor

    def cursor(self):
        return self._db_connection.cursor()

    def list_tables(self):
        return self.query("select * from sqlite_master where type = 'table' order by name")

    def get_table_ddl(self, tablename):
        sql = f'''SELECT m.name as table_name,  p.name as column_name,  p.*
                    FROM sqlite_master AS m
                    JOIN pragma_table_info(m.name) AS p
                   WHERE m.name=:tablename 
                ORDER BY m.name, p.cid'''
        param = {'tablename': tablename}
        return self.query(sql, param)

    def connection(self):
        return self._db_connection
