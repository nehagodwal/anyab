from logging import getLogger
from psycopg2.extras import RealDictCursor
from executor.config.pg_config import PostgresConfig
from executor.user_application.utils.postgre_connect import get_pg_connection
from executor.user_application.utils.shell_commands import run_cmd, run_cmd2

logger = getLogger(__name__)


class PostgresParam:
    def __init__(self, pg_config : PostgresConfig):
        self.pg_config = pg_config

    def get_current_param_value(self, param_name):
        sql_str = """SELECT * FROM pg_catalog.pg_settings WHERE name = '{0}';""".format(param_name)
        logger.info(f'Sql string is: {sql_str}')
        with get_pg_connection(connect_str=self.pg_config.pg_conn_str) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql_str)
                data = cursor.fetchone()
                logger.info(f'Fetched data: {data}')
        return data['setting']

    
    def update_param_value(self, param_name, param_value, pg_restart=False, pg_reload=False):
        update_sql = """ALTER SYSTEM SET {0} = '{1}MB';""".format(param_name, param_value)
        logger.info(f'Update sql string is: {update_sql}')
        conn = get_pg_connection(connect_str=self.pg_config.pg_conn_str)
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(update_sql)
        conn.commit()
        cursor.close()
        if pg_reload:
            logger.info('Need to reload the postgres config!')
            self._run_pg_reload()
        if pg_restart:
            logger.info('Need to restart the postgres service!')
            self._restart_pg()


    def _restart_pg(self, time_out=60):
        restart_cmd = "service postgresql restart"
        '''
        restart_cmd = "sudo -i -u {0} {1}/pg_ctl -D {2} -w -t {3} restart".format(self.pg_config.user,
                                                                                  self.pg_config.pgbin,
                                                                                  self.pg_config.pgdata,
                                                                                  time_out)
        '''
        run_cmd2(restart_cmd)
        logger.info('Restarted postgres successfully!')

    def _run_pg_reload(self):
        reload_sql = """SELECT pg_reload_conf();"""
        logger.info(f'Reload sql string is: {reload_sql}')
        with get_pg_connection(connect_str=self.pg_config.pg_conn_str) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                conn.set_session(autocommit=True)
                cursor.execute(reload_sql)
                logger.info('Reload command executed!')
