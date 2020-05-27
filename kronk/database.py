import time
from sys import exit

from config import config

from rethinkdb import r
from rethinkdb.errors import ReqlAuthError
from rethinkdb.errors import ReqlDriverError

DATABASE = 'work'
task_queue = 'tasks'
TABLES = [task_queue]
INDEXES = ["time_last"]
# TODO: Adding logging here instead of printing with flush=True
# Infact make this whole thing a class


def connect(db: str = None) -> r.connection_type:
    """ connect to database """
    conn  = None
    host  = config["rdb_endpoint"]
    passw = config["rdb_password"]

    return r.connect(host=host, password=passw, db=db)


def connect_with_retry(database):
    # TODO: Make this nicer somehow
    conn = None
    for x in range(1, 30):
        try:
            try:
                conn = connect(database)

            except ReqlAuthError:
                print("Error: Wrong password. If you are using docker-compose, check the password there!", flush=True)
                exit(1)

            except Exception:
                print(f"connecting to database - attempt {x}", flush=True)
                time.sleep(2)
                continue
            break
        except KeyboardInterrupt:
            exit(0)

    return conn

def init() -> None:
    """ Initialise database """
    print("Initialising database", flush=True)
    conn = connect_with_retry(DATABASE)

    if DATABASE not in r.db_list().run(conn):
        print(f"Creating database '{DATABASE}'", flush=True)
        r.db_create(DATABASE).run(conn)

    for table in TABLES:
        if table not in r.db(DATABASE).table_list().run(conn):
            print(f"Creating table '{table}'", flush=True)
            r.db(DATABASE).table_create(table).run(conn)

        for index in INDEXES:
            if index not in r.db(DATABASE).table(table).index_list().run(conn):
                print(f"Creating index '{index}'", flush=True)
                r.db(DATABASE).table(table).index_create(index).run(conn)


def task_get_new() -> dict:
    """ fetch a single work item in ready state """

    conn = connect(DATABASE)
    ret = r.table(task_queue).order_by(index='time_last').filter({"state": "ready"}).limit(1).run(conn)

    try:
        task = list(ret)[0]
    except IndexError:
        task = {}

    return task


def task_create(task: dict) -> None:
    """ Insert new work item """
    conn = connect(DATABASE)
    return r.table(task_queue).insert(task).run(conn)


def task_update(task: dict) -> None:
    """
    update work item state
    valid states should be: "ready", "active", "complete", "failed"
    """

    conn = connect(DATABASE)
    r.table(task_queue).insert(task, conflict="update").run(conn)


if __name__ == "__main__":
    init()
