import psycopg2
from psycopg2.extras import RealDictCursor


def get_conn_str(pg_user='postgres', pg_host='localhost', pg_pwd='postgres', pg_port='5432'):
    return "user={0} host={1} password={2} port={3}".format(pg_user, pg_host, pg_pwd, pg_port)

def get_pg_connection(connect_str="user='postgres' host='localhost' password='postgres' port='5432'"):
    return psycopg2.connect(connect_str)


if __name__ == "__main__":
    connection_str = get_conn_str()
    try:
        with get_pg_connection(connection_str) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""SELECT * FROM pg_catalog.pg_settings WHERE name = 'shared_buffers'""")
                rows = cur.fetchone()
                print(rows)
    except Exception as e:
        print(f'Error connecting the postgre database: {e}')
