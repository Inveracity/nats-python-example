import asyncio
import json
import logging
import random
import sys
import time
import traceback
import uuid

from nats.aio.client import Client as Nats

from kronk.config import Config
from kronk.database import Rethink
from kronk.kubernetes import GracefulTermination
from kronk.task import State
from kronk.task import Task

log = logging.getLogger(__name__)

config = Config()
graceful = GracefulTermination()
nc = Nats()
rdb = Rethink()


class Worker:
    def simulation(self) -> (int, str):
        """ Create a random execution time for a simulated job """

        task_shor = [1] * 60           # 60% chance of a job taking a short time
        task_medi = [2] * 30           # 30% chance of a job taking a medium time
        task_long = [3] * 10           # 10% chance of a job taking a long time
        task_fail = ["ready"] * 50     # 50% chance of a job failing, set ready state to retry the job
        task_comp = ["complete"] * 50  # 50% chance of a job completing

        task_lengths = task_shor + task_medi + task_long
        task_states = task_fail + task_comp

        task_length = random.choice(task_lengths)
        task_state = random.choice(task_states)

        return task_length, task_state

    def do_work(self, task: Task) -> Task:
        """ Simulated worker, replace this code with actual workloads """

        # Get simulation values
        length, state = self.simulation()

        # Simulate fake work on task
        time.sleep(length)

        # Set the state
        task.state = state

        # Return it to the distributor
        return task

    async def next_task(self, worker_id: str):
        """ Request a new task from the distributor """

        try:
            # Tell distributor to send a new task
            task_request = {'worker_id': worker_id, 'message': 'new'}
            payload = json.dumps(task_request)
            response = await nc.request(subject="task", payload=payload.encode(), timeout=5)
            task_id = response.data.decode()

            # If the response is nothing
            if task_id == "nothing":
                return

            log.debug(f"received task id {payload}")
            task: Task = rdb.task_get_by_id(task_id)

            if not task:
                log.fatal(f"Unable to find task in database {task_id}")
                sys.exit(1)

            task.log("info", "Processing")
            self.do_work(task)

            if task.state == State.READY and task.attempts >= 5:
                task.state = "failed"
                task.log("error", "Failed")

            if task.state == State.READY:
                task.log("warning", "Retrying")

            if task.state == State.COMPLETE:
                task.log("info", "Success")

            # Unassign worker
            task.worker_id = ""

            # Update task in database
            rdb.task_update(task.to_dict())

        except Exception:
            log.fatal(traceback.format_exc())
            sys.exit(1)

    async def main(self):
        """ Start the worker loop """
        loop = asyncio.get_running_loop()

        worker_id = str(uuid.uuid4())[:8]
        log.info(f"Starting worker {worker_id}")

        # Connect to nats servers
        await nc.connect(servers=config.NATS_ENDPOINT, loop=loop)

        while not graceful.termination:
            await self.next_task(worker_id)
            time.sleep(1)

        if graceful.termination:
            sys.exit(0)


if __name__ == '__main__':
    w = Worker()
    asyncio.run(w.main())
