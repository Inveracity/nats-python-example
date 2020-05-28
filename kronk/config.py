from os import environ

config = {
    "rdb_endpoint": environ.get("RDB_ENDPOINT", "127.0.0.1"),
    "rdb_password": environ.get("RDB_PASSWORD", None),
    "nats_endpoint": environ.get("NATS_ENDPOINT", "nats://127.0.0.1:4222/"),
}
