from dataclasses import dataclass
from os import environ


@dataclass
class Config:
    db_host: str = environ.get("DB_HOST", "127.0.0.1")
    db_port: str = environ.get("DB_PORT", "28015")
    db_pass: str = environ.get("DB_PASSWORD", None)
    nats_host: str = environ.get("NATS_HOST", "127.0.0.1")
    nats_port: str = environ.get("NATS_PORT", "4222")

    @property
    def nats_endpoint(self) -> str:
        """
        combines protocol, host and port
        """
        return f"nats://{self.nats_host}:{self.nats_port}/"
