import logging
import asyncio
import time
import json
from config import config
from database import get_work_item
from database import update_work_item_state
from nats.aio.client import Client as NATS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

nats_servers = ["nats://10.0.0.2:4222"]


async def run(loop):
    log.info(f'Starting nats client. Server: {nats_servers}')

    nc = NATS()

    await nc.connect(servers=nats_servers, loop=loop)

    async def sub(msg):
        # Process incoming message from worker
        message = json.loads(msg.data.decode())

        # If worker is ready to receive a new task, the state is "new"
        if message['state'] == "new":
            task = get_work_item()[0]

            update_work_item_state(task['id'], "active")

            print(f"sending task {task} to worker")

            await nc.publish(subject=msg.reply, payload=task.encode())

        else:
            update_work_item_state(message['id'], message['state'])

    await nc.subscribe(subject=config['subject'], queue=config['queue'], cb=sub)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.run_forever()
    loop.close()
