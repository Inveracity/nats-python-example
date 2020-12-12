from dataclasses import dataclass
from os import environ


@dataclass
class Config:
    DB_HOST: str = environ.get("DB_HOST", "127.0.0.1")
    DB_PORT: str = environ.get("DB_PORT", "28015")
    DB_PASS: str = environ.get("DB_PASSWORD", None)
    NATS_HOST: str = environ.get("NATS_HOST", "127.0.0.1")
    NATS_PORT: str = environ.get("NATS_HOST", "4222")

    @property
    def NATS_ENDPOINT(self) -> str:
        """
        combines protocol, host and port
        """
        return f"nats://{self.NATS_HOST}:{self.NATS_PORT}/"
