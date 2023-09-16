import oracledb
import pandas as pd

user = 'sys'
password = 'sys'
port = 1521
service_name = 'OEDEV'
conn_string = "localhost:{port}/{service_name}".format(port=port, service_name=service_name)

with oracledb.connect(user=user, password=password, dsn=conn_string) as conn:
    sql = """
        select current_timestamp as ts, 1 as id from dual
    """
    sql = """
        select * from user_objects order by 1
    """
    df = pd.read_sql(sql=sql, con=conn)
    print(df)
    print(pd.io.sql.get_schema(df.reset_index(), 'data'))
