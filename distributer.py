import logging
import asyncio

import time

from nats.aio.client import Client as NATS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

nats_servers = ["nats://10.0.0.2:4222"]

tasks = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']

async def run(loop):
    log.info(f'Starting nats client. Server: {nats_servers}')

    nc = NATS()

    await nc.connect(servers=nats_servers, loop=loop)

    async def sub(msg):
        task = tasks.pop(0)
        print(f"sending task {task} to worker")
        await nc.publish(subject=msg.reply, payload=task.encode())

    await nc.subscribe(subject="task", queue="worker", cb=sub)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.run_forever()
    loop.close()
