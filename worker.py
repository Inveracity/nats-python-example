import logging
import asyncio

import time

from nats.aio.client import Client as NATS

nats_servers = ["nats://10.0.0.2:4222"]
nc = NATS()

def worker(msg):
    data = msg.data.decode()
    for x in range(5):
        time.sleep(1)
        print(f"working on payload: {data} step {x}")


async def next_task():
    subject = "task"
    queue = "workers"

    try:
        print("Requesting new task")
        msg = await nc.request(subject=subject, payload=b"", timeout=1)
        worker(msg)
    except asyncio.TimeoutError:
        print("No task received")


async def main():
    await nc.connect(servers=nats_servers, loop=asyncio.get_running_loop())

    while True:
        await next_task()
        time.sleep(5)


if __name__ == '__main__':
    asyncio.run(main())

