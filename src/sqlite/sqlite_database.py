#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
""" Wrapper to call Oracle database

    usage samples:

    database = DatabaseApi(DateioDatabase.KARTON_BO_PROD, 'scripts', 'E4MMz6HZWu3l18du')
    sql = f"select count(0), max(id) from data_batch"
    df = database.query(sql)
    print(df)

    hled_id = df.iloc[-1]['max']

    params={'id' : int(hled_id)}
    sql = f"select * from data_batch where id > %(id)s - 5"
    df = database.query(sql, params)
    for index, row in df.iterrows():
        print(index, row['id'], row['version'])

    file_list = []
    file_list.append('file1')
    file_list.append('file2')

"""

import logging
import sqlite3

import pandas as pd


class SqliteDatabase(object):
    def __init__(self, sqlite_file_name):
        # check p_database_name
        self._db_connection = sqlite3.connect(sqlite_file_name)
        # self._db_connection.set_trace_callback(print)
        self._cursor = self._db_connection.cursor()

    def __del__(self):
        if self._db_connection is not None:
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
        param = {'tablename':tablename}
        return self.query(sql, param)

