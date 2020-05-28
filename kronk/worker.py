import asyncio
import json
import logging
import time
import traceback
import uuid
from random import choice
from nats.aio.client import Client as Nats
from config import config
from database import Rethink
from task import Task

# Create worker id on start
worker_id = str(uuid.uuid4())[:8]

# Set worker id in logging format
logging.basicConfig(level=logging.INFO, format=f'%(asctime)s [%(levelname)-7s] {worker_id}: %(message)s')
log = logging.getLogger(__name__)

nc  = Nats()
rdb = Rethink()


def simulation() -> (int, str):
    """ Create a random execution time for a simulated job """

    task_shor = [1] * 60           # 60% chance of a job taking a short time
    task_medi = [2] * 30           # 30% chance of a job taking a medium time
    task_long = [3] * 10           # 10% chance of a job taking a long time
    task_fail = ["ready"] * 50     # 50% chance of a job failing, set ready state to retry the job
    task_comp = ["complete"] * 50  # 50% chance of a job completing

    # Compile to lists
    task_lengths = task_shor + task_medi + task_long
    task_states  = task_fail + task_comp

    # Grab some value
    task_length = choice(task_lengths)
    task_state  = choice(task_states)

    return task_length, task_state


def worker(task: Task) -> Task:
    """ Simulated worker, replace this code with actual workloads """

    # Get simulation values
    length, state = simulation()

    # Simulate fake work on task
    time.sleep(length)

    # Set the state
    task.state = state

    # Return it to the distributor
    return task


async def next_task(worker_id: str):
    """ Request a new task from the distributor """
    task           = Task()
    task.state     = "new"
    task.worker_id = worker_id

    try:
        # Tell distributor to send a new task
        response = await nc.request(subject="task", payload=task.to_json().encode(), timeout=1)

        # Get JSON formatted data and populate task
        loaded_task   = json.loads(response.data.decode())
        task.workload = loaded_task["workload"]
        task.id       = loaded_task["id"]
        task.attempts = loaded_task["attempts"]

        log.info(f"Task BEGN: {task.id}")
        # Do work on that task
        task = worker(task)

        # Fail a task if it was attempted x times
        if task.state == "ready" and task.attempts >= 5:
            log.error(f"Task FAIL: {task.id}")
            task.state = "failed"

        # Put the task back to be picked up for another attempt
        if task.state == "ready":
            log.warning(f"Task RETR: {task.id}")

        # Mark the task as complete for no further processing
        if task.state == "complete":
            log.info(f"Task COMP: {task.id} ")

        # Update task in database
        rdb.task_update(task.to_dict())

    except asyncio.TimeoutError:
        # Simply wait for a task to come along
        log.debug("No new task")
        pass

    except Exception:
        log.fatal(traceback.format_exc())
        exit(1)


async def main():
    """ Start the worker loop """
    loop = asyncio.get_running_loop()

    log.info(f"Starting worker {worker_id}")

    # Connect to nats servers
    await nc.connect(servers=config['nats_endpoint'], loop=loop)

    while True:
        await next_task(worker_id)
        time.sleep(0.1)


if __name__ == '__main__':
    asyncio.run(main())
