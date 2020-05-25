from os import environ

config = {
    "rdb_endpoint":  environ.get("RDB_ENDPOINT", "10.0.0.2"),
    "nats_endpoint": environ.get("NATS_ENDPOINT", "nats://10.0.0.2:4222/"),
    "rdb_password":  environ.get("RDB_PASSWORD", ""),
    "subject":       "task",
    "queue":         "workers",
}

