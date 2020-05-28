import time
from random import sample
from string import ascii_letters
from uuid import uuid4

from database import Rethink
from task import Task

rdb  = Rethink()
task = Task()

for _ in range(100):
    random_chars  = sample(ascii_letters, 10)
    random_string = "".join(random_chars)
    task.workload = random_string
    task.state    = "ready"
    task.id       = str(uuid4())

    print(f"Generating task: {random_string}")

    rdb.task_create(task.to_dict())

    time.sleep(0.2)
