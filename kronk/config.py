from os import environ

config = {
    "rdb_endpoint": environ.get("RDB_ENDPOINT", "rethinkdb"),
    "rdb_password": environ.get("RDB_PASSWORD", None),
    "nats_endpoint": environ.get("NATS_ENDPOINT", "nats://nats:4222/"),
}
