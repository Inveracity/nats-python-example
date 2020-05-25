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
        print("Error: Unable to connect to server")
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

    db = r.db(DATABASE)


def get_work_item() -> dict:
    """ fetch a single work item in ready state """

    conn = connect(DATABASE)
    task = r.table(task_queue).filter({"state": "ready"}).limit(1).run(conn)

    return list(task)


def create_work_item(work_item: dict) -> None:
    """ Insert new work item """
    conn = connect(DATABASE)
    return r.table(task_queue).insert(work_item).run(conn)


def update_work_item_state(_id: str, value: str) -> None:
    """ update work item state """
    print(_id, value)
    conn = connect(DATABASE)
    res = r.table(task_queue).get(_id).update({"state": value}).run(conn)
    print(res)

if __name__ == "__main__":
    init()
