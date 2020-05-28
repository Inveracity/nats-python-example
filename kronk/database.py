import time
import logging
from sys import exit

from config import config

from rethinkdb import r
from rethinkdb.net import DefaultConnection
from rethinkdb.errors import ReqlAuthError
from rethinkdb.errors import ReqlDriverError

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)-7s]: %(message)s')
log = logging.getLogger(__name__)


class Rethink:
    def __init__(
        self,
        database='work',
        table='tasks',
        user="admin",
        password=None,
        indexes=['time_last']
    ):
        self.HOST    = config["rdb_endpoint"]
        self.PW      = config['rdb_password']
        self.USER    = user
        self.DB      = database
        self.TABLE   = table
        self.INDEXES = indexes

        self.conn = DefaultConnection(
            host=self.HOST,
            port=28015,
            db=self.DB,
            auth_key=None,
            user=self.USER,
            password=self.PW,
            timeout=None,
            ssl=None,
            _handshake_version=None
        )

        self.connect_with_retry()

        try:
            log.info("rethinkdb initialising")

            # Create databases
            db_exists = r.db_list().contains(self.DB).run(self.conn)
            if not db_exists:
                log.info(f'creating database {self.DB}')
                r.db_create(self.DB).run(self.conn)

            # Create tables
            table_exists = r.db(self.DB).table_list().contains(self.TABLE).run(self.conn)

            if not table_exists:
                log.info(f'adding table {self.TABLE}')
                r.db(self.DB).table_create(self.TABLE).run(self.conn)

            # Create indexes
            rtable = r.db(self.DB).table(self.TABLE)

            current_indexes = rtable.index_list().run(self.conn)
            for index in self.INDEXES:
                if index not in current_indexes:
                    log.info(f'adding index {index}')
                    rtable.index_create(index).run(self.conn)

            log.info("rethinkdb ready")

        except ReqlDriverError as err:
            log.error(f"rethinkdb failed to initialise: {err}")
            exit(1)

    def connect(self):
        if self.conn.is_open():
            self.conn.close()

        self.conn = r.connect(host=self.HOST, db=self.DB, user=self.USER, password=self.PW)

    def connect_with_retry(self):
        """ Attempt to reconnect """
        for x in range(10):
            try:
                try:
                    self.connect()

                except ReqlAuthError as err:
                    log.fatal(err)
                    exit(1)

                except Exception:
                    log.info(f"connecting to database - attempt {x}")
                    time.sleep(2)
                    continue
                break

            except KeyboardInterrupt:
                exit(0)

    def task_get_new(self) -> dict:
        """ fetch a single work item in ready state """

        self.connect_with_retry()

        t = r.table(self.TABLE)
        t.wait(timeout=1).run(self.conn)  # wait for shards to be ready
        ret = t.order_by(index='time_last').filter({"state": "ready"}).limit(1).run(self.conn)

        try:
            task = list(ret)[0]
        except IndexError:
            task = {}

        return task

    def task_create(self, task: dict) -> None:
        """ Insert new work item """

        self.connect_with_retry()
        return r.table(self.TABLE).insert(task).run(self.conn)

    def task_update(self, task: dict) -> None:
        """
        update work item state
        valid states should be: "ready", "active", "complete", "failed"
        """

        self.connect_with_retry()
        r.table(self.TABLE).insert(task, conflict="update").run(self.conn)
