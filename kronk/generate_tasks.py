import time
from random import sample
from string import ascii_letters
from uuid import uuid4

from database import task_create
from task import Task

task = Task()

for x in range(100):
    random_chars  = sample(ascii_letters, 10)
    random_string = "".join(random_chars)
    task.workload = random_string
    task.state    = "ready"
    task.id       = str(uuid4())

    print(f"Generating task: {random_string}")

    task_create(task.to_dict())

    time.sleep(0.2)
