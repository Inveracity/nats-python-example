import logging
from random import sample
from string import ascii_letters
from time import sleep
from uuid import uuid4

from kronk.database import Rethink
from kronk.task import State
from kronk.task import Task

log = logging.getLogger(__name__)

rdb = Rethink()

for _ in range(100):
    task = Task()
    random_chars = sample(ascii_letters, 10)
    random_string = "".join(random_chars)
    task.workload = random_string
    task.state = State.READY
    task.id = str(uuid4())

    log.info(f"Generating task: {random_string}")

    rdb.task_create(task)

    sleep(0.2)
