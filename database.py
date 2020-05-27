from sys import exit

from config import config

from rethinkdb import r
from rethinkdb.errors import ReqlAuthError
from rethinkdb.errors import ReqlDriverError

DATABASE = 'work'
task_queue = 'tasks'
TABLES = [task_queue]


def connect(db: str = None) -> r.connection_type:
    """ connect to database """
    conn  = None
    host  = config["rdb_endpoint"]
    passw = config["rdb_password"]

    try:
        conn = r.connect(host=host, password=passw, db=db)

    except ReqlAuthError:
        print("Error: Wrong password. If you are using docker-compose, check the password there!")
        exit(1)

    except ReqlDriverError:
        print("Error: Unable to connect to rethinkdb")
        exit(1)

    return conn


def init() -> None:
    """ Initialise database """

    conn = connect(DATABASE)

    if DATABASE not in r.db_list().run(conn):
        print(f"Creating database '{DATABASE}'")
        r.db_create(DATABASE).run(conn)

    for table in TABLES:
        if table not in r.db(DATABASE).table_list().run(conn):
            print(f"Creating table '{table}'")
            r.db(DATABASE).table_create(table).run(conn)


def task_get_new() -> dict:
    """ fetch a single work item in ready state """

    conn = connect(DATABASE)
    ret = r.table(task_queue).filter({"state": "ready"}).limit(1).run(conn)

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
