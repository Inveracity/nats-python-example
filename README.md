# nats-python-example

Working out the best way to do request/reply for distributing tasks

>So this turned out to be more than just nats and python by introducing Rethinkdb.

![](docs/images/gif.gif)

## Dependencies

- python 3.8
- docker-compose


## Install requirements

```bash
pip install pipenv
pipenv install
```

## Run the backend

This starts NATS2 and Rethinkdb 2.4.0

```bash
docker-compose up -d
```

## Run the code

Put some fake tasks in the database

```bash
pipenv run generate
```

Start the distributor

```bash
pipenv run distributor
```

Start a worker

```bash
pipenv run worker
```

## Rethinkdb

You can open the rethinkdb webinterface with `http://localhost:8080`

In the data explorer try the query

```javascript
r.db("work").table("tasks").changes()
```

and press the `run` button to watch work happening in realtime

![](docs/images/rethinkdb.gif)
