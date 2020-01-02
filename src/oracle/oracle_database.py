#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
""" Wrapper to call Sqlite database

    usage samples:

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

import cx_Oracle
import pandas as pd


# noinspection SpellCheckingInspection
class OracleDatabase(object):
    def __init__(self, connection_string, mode=cx_Oracle.SYSDBA):
        # check p_database_name
        self._db_connection = None
        self._full_connect = connection_string
        self._db_connection = cx_Oracle.connect(self._full_connect, mode=mode)
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

    def object_exists(self, schema, obj_name, obj_type):
        sql = 'select * from all_objects where object_name=:name and object_type=:type and owner=:schema'
        params = {'name': obj_name.upper(), 'schema': schema.upper(), 'type': obj_type.upper()}
        count = self.query_ret_rownum(sql, params)
        if count == 1:
            return True
        return False

    def drop_if_exists(self, schema, obj_name, obj_type):
        if self.object_exists(schema, obj_name, obj_type):
            self.query(f'drop {obj_type} {schema}.{obj_name}')
