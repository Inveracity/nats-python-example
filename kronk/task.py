import inspect
from datetime import datetime
from json import dumps


class Task:
    def __init__(self):
        self.id        = ""
        self.state     = ""
        self.workload  = ""
        self.worker_id = ""
        self.attempts  = 0

    def time(self):
        return datetime.now().strftime("%Y%m%d%H%M%S")

    @property
    def time_last(self):
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

    def to_json(self) -> str:
        return dumps(self.to_dict())
