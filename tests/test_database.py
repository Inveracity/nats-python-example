from random import sample
from string import ascii_letters
from uuid import uuid4

from mockthink import MockThink

from kronk.database import Rethink
from kronk.task import State
from kronk.task import Task


def make_task() -> dict:
    """
    Generate a task for testing
    """
    task = Task()
    random_chars = sample(ascii_letters, 10)
    random_string = "".join(random_chars)
    task.workload = random_string
    task.state = State.READY
    task.id = str(uuid4())

    return task


random_task1 = make_task().to_dict()
random_task2 = make_task().to_dict()

task_with_specific_id = make_task().to_dict()
task_with_specific_id["id"] = "1234"

r = Rethink()

db = MockThink({
    "dbs": {
        "work": {
            "tables": {
                "tasks": [
                    random_task1,
                    random_task2,
                    task_with_specific_id,
                ]
            }
        }
    }
})


def test_task_get_new(mocker):
    """
    Test getting a task from the database
    """

    with db.connect() as conn:
        mocker.patch.object(r, "conn", conn)

    r.initialise()
    res: Task = r.task_get_new()

    assert res.id == random_task1["id"]


def test_task_get_by_id(mocker):
    """
    test task_get_by_id
    """
    with db.connect() as conn:
        mocker.patch.object(r, "conn", conn)

    res: Task = r.task_get_by_id("1234")

    assert res.id == "1234"


def test_task_create(mocker):
    """
    test task_create
    """
    with db.connect() as conn:
        mocker.patch.object(r, "conn", conn)

    task = make_task()
    task.id = "a_new_task"

    r.task_create(task)

    res: Task = r.task_get_by_id("a_new_task")

    assert res.id == "a_new_task"


def test_task_update(mocker):
    """
    test task_update
    """
    with db.connect() as conn:
        mocker.patch.object(r, "conn", conn)

    task = r.task_get_by_id("1234")
    assert task.state == State.READY

    task.state = State.COMPLETE
    r.task_update(task.to_dict())

    task = r.task_get_by_id("1234")
    assert task.state == State.COMPLETE


def test_task_assign_worker(mocker):
    """
    test task_assign_worker
    """
    with db.connect() as conn:
        mocker.patch.object(r, "conn", conn)

    task = r.task_get_by_id("1234")
    task.worker_id = "aworker"

    # New assignment
    res = r.task_assign_worker(task)
    assert res is True

    # Already assigned
    res = r.task_assign_worker(task)
    assert res is False
