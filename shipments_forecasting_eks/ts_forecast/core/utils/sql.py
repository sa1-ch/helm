import sqlalchemy
import yaml


class DBConnection:
    """ Class to hold onto DB connection state.
    """

    def __init__(self, uri):
        self.engine = sqlalchemy.create_engine(uri)
        conn = self.engine.connect()
        self.dbapi_connection = conn.connection
        if "sqlite" in self.engine.driver:
            self.driver = "sqlite3"
        else:
            self.driver = self.engine.driver
        self.uri = uri

    @classmethod
    def from_config_file(cls, cfg_file, db_prefix=""):
        with open(cfg_file, "r") as fp:
            cfg = yaml.load(fp)
        uri = cfg["DB_URI"].format(**cfg)
        if db_prefix:
            uri = cfg[db_prefix + "_DB_URI"].format(**cfg)
        else:
            uri = cfg["DB_URI"].format(**cfg)
        return cls(uri)
