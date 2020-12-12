from datetime import datetime
import inspect
import logging

from rethinkdb import r

logger = logging.getLogger(__name__)


class Task:

    def __init__(self):
        self.id = ""
        self.state = ""
        self.workload = ""
        self.worker_id = ""
        self.attempts = 0
        self.time_created: datetime = self.time()

    def time(self):
        """
        Rethinkdb compatible datetime
        """
        return datetime.now(r.make_timezone('00:00'))

    @property
    def timestamp_updated(self):
        return self.time()

    def to_dict(self) -> dict:
        """
        Dynamically update timestamp by fetching the
        class property and apply it as if it was an attribute
        """
        # make a dict of @properties
        properties = inspect.getmembers(self.__class__, lambda o: isinstance(o, property))
        property_dict = {name: prop.fget(self) for name, prop in properties}

        # Combine property dict with normal attribute dict
        superdict = self.__dict__
        superdict.update(property_dict)
        return superdict

    def from_dict(self, d):
        """
        Convert from a dictionary object to class properties
        """
        self.id = d.get('id')
        self.state = d.get('state')
        self.attempts = d.get('attempts', 0)
        self.worker_id = d.get('worker_id')
        self.workload = d.get('workload')

        return self

    def log(self, level: str, message: str) -> None:
        """
        Logging with metadata included
        """
        msg = f"[{self.timestamp_updated}] [{self.id}] [{self.state}]: {message}"

        logit = {
            "debug": logger.debug,
            "info": logger.info,
            "warning": logger.warning,
            "error": logger.error,
            "fatal": logger.fatal,
        }

        logit[level](msg)


class State:
    READY = "ready"
    COMPLETE = "complete"
    FAILED = "failed"
