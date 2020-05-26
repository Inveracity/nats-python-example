import asyncio
import json
import logging
import time
import traceback
import uuid
from random import choice

from nats.aio.client import Client as NATS

from config import config
from database import task_update
from task import Task

nats_servers = ["nats://10.0.0.2:4222"]
nc = NATS()

# For tracing logs a unique ID is create on start,
# to ensure events occured as expected between worker and distributor
worker_id = str(uuid.uuid4())[:8]

logging.basicConfig(level=logging.INFO, format=f'%(asctime)s [%(levelname)s] {worker_id}: %(message)s')
log = logging.getLogger(__name__)


def simulation() -> (str, str):
    """ Create a random execution time for a simulated job """

    task_short    = [1] * 60  # 60% chance of a job taking a short time
    task_medium   = [2] * 30  # 30% chance of a job taking a medium time
    task_long     = [3] * 10  # 10% chance of a job taking a long time
    task_fail     = ["ready"] * 50  # 50% chance of a job failing, set ready state to retry the job
    task_complete = ["complete"] * 50  # 50% chance of a job completing

    # Compile to lists
    task_lengths = task_short + task_medium + task_long
    task_states   = task_fail + task_complete

    # Grab some value
    task_length = choice(task_lengths)
    task_state = choice(task_states)

    return task_length, task_state


def worker(task):
    """ Simulated worker, replace this code with actual workloads """

    # Simulate fake work on task
    length, state = simulation()

    log.info(f"starting work on task: {task.workload}")

    for _ in range(length):
        time.sleep(1)

    # Set the state
    task.state = state

    # Return it to the distributor
    return task


async def next_task(worker_id):
    task           = Task()
    task.state     = "new"
    task.worker_id = worker_id

    try:
        # Tell distributor to send a new_task task
        response = await nc.request(subject=config['subject'], payload=task.to_json().encode(), timeout=10)

        # Get JSON formatted data and populate task
        loaded_task   = json.loads(response.data.decode())
        task.workload = loaded_task["workload"]
        task.id       = loaded_task["id"]
        task.attempts = loaded_task["attempts"]

        # Do work on that task
        task = worker(task)

        # Fail a task if it was attempted 2 times and failed both
        if task.state == "ready" and task.attempts >= 5:
            task.state = "failed"
            log.error(f"Task failed: {task.id}")

        # Update task state
        task_update(task.to_dict())

    except asyncio.TimeoutError:
        # Simply waiting for a task to come along
        log.debug("No new task")
        pass

    except Exception:
        log.error(traceback.format_exc())
        exit(1)


async def main():
    loop = asyncio.get_running_loop()

    log.info(f"Starting worker {worker_id}")
    await nc.connect(servers=nats_servers, loop=loop)

    while True:
        await next_task(worker_id)
        time.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
