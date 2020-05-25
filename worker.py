import logging
import asyncio
import json
import time

from config import config
from nats.aio.client import Client as NATS

nats_servers = ["nats://10.0.0.2:4222"]
nc = NATS()

def worker(msg):
    # Get JSON formatted data
    print("start work")
    task = json.loads(msg.data.decode())


    # Simulate fake work on task
    for x in range(5):
        print(f"working on payload: {task['task']} step {x}")
        time.sleep(2)

    # Set the state to complete
    task['state'] = "complete"

    # Return it to the distributor
    return json.dumps(task)


async def next_task():
    print("Requesting new task")
    new = json.dumps({"state": "new"})

    try:

        # Tell distributor to send a new task
        msg = await nc.request(subject=config['subject'], payload=new.encode(), timeout=1)
        print(msg)

        # Do work on that task
        worker(msg)
        print(result)
        # Send the result of the task back to the distributor
        #await nc.publish(subject=config['subject'], payload=result.encode())

    except asyncio.TimeoutError:
        # Simply waiting for a task come along
        pass


async def main():
    await nc.connect(servers=nats_servers, loop=asyncio.get_running_loop())

    while True:
        await next_task()
        time.sleep(5)


if __name__ == '__main__':
    asyncio.run(main())

