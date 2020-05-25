import time

from database import create_work_item
from database import get_work_item

for x in range(100):
    work_item = {
        "task": x,
        "state": "ready"
    }

    print(f"Generating task: {x}")
    ret = create_work_item(work_item)
    print(f"created: {ret['generated_keys']}")
    time.sleep(2)
