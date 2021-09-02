from executor.config.config import Config
from executor.user_application.utils.postgre_connect import get_conn_str


class PostgresConfig(Config):
    def __init__(self, conf_path, section='PostgreSQL'):
        super().__init__(conf_path)
        self.config_dict = dict(self.config.items(section))

    @property
    def pgdata(self):
        return "{0}/{1}/{2}".format(self.get_parameter_value('pgdata'),
                                    self.get_parameter_value('pg_version'),
                                    'main')

    @property
    def pgbin(self):
        return "{0}/{1}/{2}".format(self.get_parameter_value('pgbin'),
                                    self.get_parameter_value('pg_version'),
                                    'bin')

    @property
    def major_version(self):
        return self.get_parameter_value('pg_version')

    @property
    def host(self):
        return self.get_parameter_value('pghost')

    @property
    def port(self):
        return self.get_parameter_value('pgport')

    @property
    def user(self):
        return self.get_parameter_value('pguser')

    @property
    def password(self):
        return self.get_parameter_value('pgpassword')

    @property
    def database(self):
        return self.get_parameter_value('pgdatabase')

    @property
    def pg_conn_str(self):
        return get_conn_str(pg_user=self.user, pg_host=self.host, pg_pwd=self.password, pg_port=self.port)
