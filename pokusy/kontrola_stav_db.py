#!/usr/bin/python
# -*- coding: windows-1250 -*-
#
# pro vsechny DBOE v NOE,ACC a PRO spusti dotazy pro zjisteni stavu DB
#

import datetime
import os

import oracledb
import pandas as pd
import getpass
import logging

dotazy = [('Nazev instance', 'select ora_database_name, user, systimestamp from dual'),
          ('Statistiky tabulek',
           """
               SELECT owner,table_name,partition_name,object_type,num_rows,blocks,empty_blocks,last_analyzed
                 FROM all_tab_statistics a
                WHERE owner in ( 'BSP', 'OES', 'ICMADMIN', 'RMADMIN', 'POWER_GUI')
                  AND num_rows is not null
                  AND num_rows > 0
                ORDER BY a.last_analyzed desc
           """
           ),
          ('Invalidni objekty',
           """
            SELECT  OWNER, OBJECT_NAME, OBJECT_TYPE, STATUS
            FROM    DBA_OBJECTS
            WHERE   STATUS = 'INVALID'
            ORDER BY OWNER, OBJECT_TYPE, OBJECT_NAME
            """
           ),
          ('Volne misto',
           """
           SELECT
               f.tablespace_name,
               TO_CHAR( (t.total_space - f.free_space),'999,999') "USED (MB)",
               TO_CHAR(f.free_space,'999,999') "FREE (MB)",
               TO_CHAR(t.total_space,'999,999') "TOTAL (MB)",
               TO_CHAR( (round( (f.free_space / t.total_space) * 100) ),'999')
               || ' %' per_free
           FROM
               (
                   SELECT
                       tablespace_name,
                       round(SUM(blocks * (
                           SELECT
                               value / 1024
                           FROM
                               v$parameter
                           WHERE
                               name = 'db_block_size'
                       ) / 1024) ) free_space
                   FROM
                       dba_free_space
                   GROUP BY
                       tablespace_name
               ) f,
               (
                   SELECT
                       tablespace_name,
                       round(SUM(bytes / 1048576) ) total_space
                   FROM
                       dba_data_files
                   GROUP BY
                       tablespace_name
               ) t
           WHERE
               f.tablespace_name = t.tablespace_name
               AND ( round( (f.free_space / t.total_space) * 100) ) < 10
           """)
          ]


def xprint(arg):
    logging.info(arg)


def print_query_result(p_db, p_query, msg=None):
    if msg:
        xprint(f'*** {msg} ')
    df = pd.read_sql(p_query, p_db, params=None)
    with pd.option_context('display.max_rows', 10, 'display.max_columns', None, 'display.width',
                           1000):  # more options can be specified also
        if not df.empty:
            xprint(df)
    xprint('--')


def check_ora_database_name(db_in_tns, pwd):
    xprint(db_in_tns)
    connection = oracledb.connect(f'nemecd/{pwd}@' + db_in_tns)
    for name, sql_query in dotazy:
        print_query_result(connection, sql_query, name)


def main():
    user = getpass.getuser()

    pwd = getpass.win_getpass("User Name : %s" % user)

    for env in ['NOE', 'ACC', 'PRO']:
        for db_inst in ['OEICM01', 'OEICM02', 'OE', 'OEPUG', 'OEMIG']:
            bExistuje = True
            ##            neexistujici kombinace
            if env in ['PRO', 'ACC'] and db_inst == 'OEPUG':
                bExistuje = False
            if env in ['NOE'] and db_inst == 'OEMIG':
                bExistuje = False

            if bExistuje:
                full_inst_name = f'{db_inst}{env}.WORLD'
                if (env == 'ACC' and db_inst == 'OEPUG') == False:
                    if (env == 'PRO' and db_inst == 'OEPUG') == False:
                        check_ora_database_name(full_inst_name, pwd)
                        xprint(
                            '---------------------------------------------------------------------------------------------------')


if __name__ == '__main__':
    logging.basicConfig(
        filename=f"kontrola_db_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.log",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format='%(message)s'
    )
    logging.getLogger().addHandler(logging.StreamHandler())

    source_dir_name = os.getcwd()
    target_dir_name = os.path.abspath(os.path.join(os.getcwd(), "../src"))

    main()
    logging.info(r"OK vse hotovo")
