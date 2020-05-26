import asyncio
import json
import logging
import traceback

from nats.aio.client import Client as NATS

from config import config
from database import task_get_new, task_update
from task import Task

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

nc           = NATS()
nats_servers = config['nats_endpoint']
subject      = config.get("subject", "task")
queue        = config.get("queue")
worker_id    = None
task_id      = None
state        = None


async def run(loop):
    log.info(f'Starting nats client. Server: {nats_servers}')
    await nc.connect(servers=nats_servers, loop=loop)
    await nc.subscribe(subject=config['subject'], queue=config['queue'], cb=sub)


async def sub(msg):
    task = Task()

    try:
        # Process incoming message from worker
        message = json.loads(msg.data.decode())

        task.worker_id = message["worker_id"]
        task.state     = message['state']
        task.id        = message['id']

        # If worker is ready to receive a new task, the state is "new"
        # else update the task with the status received from the worker
        if task.state == "new":
            # Get a new task
            payload = prep_task(task)

            # Send the task to worker
            if payload:
                await nc.publish(subject=msg.reply, payload=payload.encode())

    except Exception:
        log.error(traceback.format_exc())


def prep_task(task: Task) -> str:
    """
    Fetch a task from the database and convert it to JSON
    Increment the attempts by 1 to keep track of task retries
    """

    # Get new work item from database
    new_task = task_get_new()

    # If nothing is available return empty string
    if not new_task:
        return ""

    else:
        task.id       = new_task['id']
        task.workload = new_task['workload']
        task.attempts = new_task["attempts"] + 1
        task.state    = "active"

        # Set work item state to active
        task_update(task.to_dict())

        log.info(f"Sending task: {task.workload} to worker: {task.worker_id}")

        return task.to_json()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.run_forever()
    loop.close()
