import asyncio
import json
import logging
import traceback
from typing import Optional

from nats.aio.client import Client as NATS

from kronk.config import Config
from kronk.database import Rethink
from kronk.task import Task

log = logging.getLogger(__name__)

config = Config()
nc = NATS()
rdb = Rethink()

rdb.initialise()


class Distributor:
    """
    The Distributor receives requests for new work
    from the workers and sends back a task ID for the
    worker to process.
    """

    def prep_task(self, worker_id: str) -> Optional[str]:
        """
        Assign task to worker
        """
        task: Task = rdb.task_get_new()
        log.debug(task)
        if not task:
            return "nothing"

        task.worker_id = worker_id
        assigned: bool = rdb.task_assign_worker(task)

        if not assigned:
            task.log("warning", f"Task is already assigned to worker {task.worker_id}")
            return "nothing"

        task.log("info", f"Assigned worker {task.worker_id}")

        return task.id

    async def sub(self, msg):
        """
        Callback function called for every message
        coming in from the workers requesting new work
        """
        try:
            # Process request for task from worker
            request = json.loads(msg.data.decode())

            if request['message'] == "new":
                worker_id = request['worker_id']

                task_id = self.prep_task(worker_id)

                await nc.publish(subject=msg.reply, payload=task_id.encode())

        except Exception as e:
            error_str = f"the Distributor threw an unhandled exception:\n{e}\n{traceback.format_exc()}\n{e.args}"
            log.error(error_str)

            raise

    async def main(self, loop):
        """
        This is the main loop that connects to the NATS message queue
        """

        log.info(f"Starting nats client. Server: {config.NATS_ENDPOINT}")
        await nc.connect(servers=[config.NATS_ENDPOINT], loop=loop)

        log.info(f"Connected to {config.NATS_ENDPOINT}")
        await nc.subscribe(subject="task", queue="workers", cb=self.sub)


if __name__ == "__main__":
    d = Distributor()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(d.main(loop))
    loop.run_forever()
    loop.close()
