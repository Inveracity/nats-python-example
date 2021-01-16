import logging
import sys
import time
from typing import Optional
import traceback

from rethinkdb import r
from rethinkdb.errors import ReqlAuthError
from rethinkdb.errors import ReqlDriverError
from rethinkdb.net import DefaultConnection

from kronk.config import Config
from kronk.task import Task

config = Config()

log = logging.getLogger(__name__)


def rdb_connection(func):
    """
    Decorator for handling connection retries
    """

    def inner_function(self, *args, **kwargs):
        try:
            # Attempt connecting to rethinkdb
            self.connect_with_retry()

            # wait for shards to be ready
            self.t.wait(timeout=4).run(self.conn)

            # run the query
            return func(self, *args, **kwargs)

        except Exception:
            log.error(f"Error occured in function call {func.__name__}:\n {traceback.format_exc()}")

    return inner_function


class Rethink:
    def __init__(
        self,
        database='work',
        table='tasks',
        user="admin",
        password=None,
        indexes=['timestamp_updated']
    ):
        self.HOST = config.DB_HOST
        self.PW = config.DB_PASS
        self.USER = user
        self.DB = database
        self.TABLE = table
        self.INDEXES = indexes
        self.t = r.db(self.DB).table(self.TABLE)

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

    def initialise(self):
        """
        Set up database with tables and indexes
        """

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
            sys.exit(1)

    def connect(self):
        if self.conn.is_open():
            self.conn.close()

        self.conn = r.connect(host=self.HOST, db=self.DB, user=self.USER, password=self.PW)

    def connect_with_retry(self):
        """ Attempt to reconnect """
        for x in range(10):
            try:
                try:
                    if not self.conn.is_open():
                        self.connect()

                except ReqlAuthError as err:
                    log.fatal(err)
                    sys.exit(1)

                except Exception:
                    log.info(f"connecting to database - attempt {x}")
                    time.sleep(2)
                    continue
                break

            except KeyboardInterrupt:
                sys.exit(0)

    @rdb_connection
    def task_get_new(self) -> Task:
        """
        fetch a single work item in ready state
        """
        ret = self.t.order_by(index='timestamp_updated').filter({"state": "ready", "worker_id": ""}).limit(1).run(self.conn)

        try:
            task = Task().from_dict(list(ret)[0])

        except IndexError:
            task = None

        return task

    @rdb_connection
    def task_get_by_id(self, task_id: str) -> Optional[Task]:
        """
        Get task by ID

        Used by the worker to query for the task using
        the task ID received from the distributor
        """
        ret = self.t.get(task_id).run(self.conn)

        if ret is None:
            return None
        task = Task().from_dict(ret)
        return task

    @rdb_connection
    def task_create(self, task: Task) -> None:
        """ Insert new work item """
        return self.t.insert(task.to_dict()).run(self.conn)

    @rdb_connection
    def task_update(self, task: dict) -> None:
        """
        update work item state
        valid states should be: "ready", "active", "complete", "failed"
        """
        self.t.insert(task, conflict="update").run(self.conn)

    @rdb_connection
    def task_assign_worker(self, task: Task) -> bool:
        """
        Ensure task is only assigned one worker
        """

        ret = self.t.get(task.id).run(self.conn)

        worker_id = dict(ret)['worker_id']

        if worker_id != "":
            return False

        worker = {"worker_id": task.worker_id}
        self.t.get(task.id).update(worker, return_changes=False).run(self.conn)

        return True
