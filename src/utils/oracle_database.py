#!/usr/bin/env python
# -*- coding: windows-1250 -*-

""" Wrapper to call Oracle database
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
import re

import cx_Oracle
import pandas as pd

from src.utils.file import str_to_file


def output_type_handler(cursor, name, default_type, size, precision, scale):
    if default_type == cx_Oracle.CLOB:
        return cursor.var(cx_Oracle.LONG_STRING, arraysize=cursor.arraysize, encodingErrors='replace')
    if default_type == cx_Oracle.BLOB:
        return cursor.var(cx_Oracle.LONG_BINARY, arraysize=cursor.arraysize)
    if default_type == cx_Oracle.LOB:
        return cursor.var(cx_Oracle.LONG_BINARY, arraysize=cursor.arraysize)
    if default_type == cx_Oracle.LONG_STRING:
        return cursor.var(cx_Oracle.LONG_STRING, arraysize=cursor.arraysize, encodingErrors='replace')
    if default_type not in (cx_Oracle.DATETIME, cx_Oracle.NUMBER, cx_Oracle.STRING, cx_Oracle.FIXED_CHAR):
        str_err = f"Neznámý typ name:{name} default_type:{default_type} size:{size} precision:{precision} scale:{scale}"
        raise Exception(str_err)


# noinspection SpellCheckingInspection
class OracleDatabase(object):
    def __init__(self, connection_string, mode=cx_Oracle.DEFAULT_AUTH):
        # possible mode cx_Oracle.SYSDBA
        self._db_connection = None
        self._full_connect = connection_string
        self._db_connection = cx_Oracle.connect(self._full_connect, mode=mode, encoding="windows-1250",
                                                nencoding="UTF-16")
        self._db_connection.outputtypehandler = output_type_handler
        self._cursor = self._db_connection.cursor()
        self.dummy_blob = self._cursor.var(cx_Oracle.BLOB)

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
        pd.set_option("display.max_colwidth", 10000)
        pd.set_option("display.colheader_justify", 'right')
        df = pd.read_sql(p_query, self._db_connection, params=p_params)
        return df

    def query_ret_rownum(self, p_query, p_params=None):
        """execute query and return only number of rows in result"""
        df = self.query(p_query, p_params)
        return len(df.index)

    def query_to_string(self, p_query, p_params=None):
        """execute query and return only number of rows in result"""
        df = self.query(p_query, p_params)
        # return df.to_string(header=False, index=False, index_names=False)
        return df.iloc[:, 0].str.cat(sep='\n')

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

    def execute(self, sql, params={}):
        """Executes a raw query"""
        try:
            self._cursor.execute(sql, params)
        except Exception as e:
            raise e
        return self._cursor

    def exec_ddl(self, sql):
        """Executes a raw query"""
        try:
            self._cursor.executemany(sql, [])
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
            self.execute(f'drop {obj_type} {schema}.{obj_name}')

    def get_object_list(self, schema, obj_type):
        sql = ("select * from dba_objects"
               " where object_type=:type"
               "   and owner=:schema"
               "   and object_name not like '%=='"
               "   and object_name not like 'SYS!_PLSQL!_%'  escape '!'"
               " order by owner, object_type, object_name")
        params = {"schema": schema, "type": obj_type}
        return self.query(sql, params)

    def tables_with_fk_list(self, schema):
        sql = """select distinct(o.object_name)
              from dba_objects o
              join dba_constraints c on c.owner = o.owner and c.table_name = o.object_name
              JOIN dba_constraints cr on cr.owner = c.r_owner and cr.constraint_name = c.r_constraint_name
             where o.object_type='TABLE'
               and o.owner=:schema
               and c.constraint_type = 'R'
               order by 1"""
        params = {'schema': schema.upper()}
        return self.query(sql, params)

    def callfunc(self, p_func_name, p_binds, p_ret_type=cx_Oracle.CLOB):
        result = self._cursor.callfunc(p_func_name, p_ret_type, keywordParameters=p_binds)
        return result

    def callproc(self, p_proc_name, p_binds):
        self._cursor.callproc(p_proc_name, keywordParameters=p_binds)

    def write_return_ddl_to_file(self, db_function, binds, full_filename):
        # get DDL from db function
        ddl = self.callfunc(db_function, p_binds=binds, p_ret_type=cx_Oracle.CLOB)
        # write clob to file
        self.clob_to_file(ddl, full_filename)

    def dbms_metadata_get_ddl(self, binds):
        ddl_clob = self.callfunc('DBMS_METADATA.GET_DDL', p_binds=binds, p_ret_type=cx_Oracle.CLOB)
        return ddl_clob

    def dbms_metadata_ddl_to_file(self, binds, full_filename):
        # get DDL from db function
        ddl = self.callfunc('DBMS_METADATA.GET_DDL', p_binds=binds, p_ret_type=cx_Oracle.CLOB)
        # write clob to file
        self.clob_to_file(ddl, full_filename)

    def dbms_metadata_set_transform_params(self, trans_params=None):
        # get DDL from db function
        if trans_params is not None:
            for key, value in trans_params.items():
                # přepsáno na anonymní blok - nefungvalo s oci.dll z Oracle19
                #  končilo to cx_Oracle.DatabaseError: ORA-03115: nepodporovaný síťový datový typ nebo reprezentace
                #
                statement = f'''
                  BEGIN
                      DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'{key}',{str(value)});
                  END;
                '''
                # self.callproc('DBMS_METADATA.SET_TRANSFORM_PARAM', binds)
                self._cursor.execute(statement)

    @staticmethod
    def clob_to_file(clob, full_filename):
        # nutno cist cely CLOB pro prevod do str
        if clob is not None:
            try:
                full_str = clob.read()
                str_to_file(full_str, full_filename)
            except UnicodeDecodeError:
                str_clob = f'CLOB UnicodeDecodeError(type={type(clob)}) write RAW to file:{full_filename}'
                logging.error(str_clob)

    def conection_instance_name(self):
        return re.split('@', self._full_connect)[1]

    def table_pk_cols(self, owner, table, alias=''):
        s_alias = alias + '.' if len(alias) > 0 else ''
        sql = ("SELECT listagg(:s_alias||cols.column_name, ', ')"
               "         within GROUP( ORDER BY cols.table_name, cols.position)"
               "  FROM all_constraints cons, all_cons_columns cols"
               " WHERE cols.table_name = :name"
               "   AND cons.constraint_type = :type"
               "   AND cons.constraint_name = cols.constraint_name"
               "   AND cons.owner = :owner")
        par = {'name': table.upper(), 'owner': owner.upper(), 'type': 'P', 's_alias': s_alias}
        s_ret = self.query_to_string(sql, par)
        return s_ret

    def table_ut_pk_update(self, owner, table):
        sql = ("SELECT listagg(cols.column_name||'= -'||cols.column_name, ', ')"
               "         within GROUP( ORDER BY cols.table_name, cols.position)"
               "  FROM all_constraints cons, all_cons_columns cols"
               " WHERE cols.table_name = :name"
               "   AND cons.constraint_type = :type"
               "   AND cons.constraint_name = cols.constraint_name"
               "   AND cons.owner = :owner")
        par = {'name': table.upper(), 'owner': owner.upper(), 'type': 'P'}
        s_ret = self.query_to_string(sql, par)
        return s_ret

    def table_where_for_pk(self, owner, table, table_alias, record_alias):
        sql = (
            "SELECT listagg(:table_alias||'.'||cols.column_name||' = '||:record_alias||'.'||cols.column_name, ' AND ')"
            "         within GROUP( ORDER BY cols.table_name, cols.position)"
            "  FROM all_constraints cons, all_cons_columns cols"
            " WHERE cols.table_name = :name"
            "   AND cons.constraint_type = :type"
            "   AND cons.constraint_name = cols.constraint_name"
            "   AND cons.owner = :owner")
        par = {'name': table.upper(), 'owner': owner.upper(), 'type': 'P', 'table_alias': table_alias,
               'record_alias': record_alias}
        # $where_for_pk
        s_ret = self.query_to_string(sql, par)
        return s_ret
