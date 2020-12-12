import logging
import signal

log = logging.getLogger(__name__)


class GracefulTermination:
    """
    When a termination signal is received
    ensure the current task finishes before
    the process is terminated
    """
    termination = False
    signals = {
        signal.SIGINT: 'SIGINT',
        signal.SIGTERM: 'SIGTERM'
    }

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        log.debug(f"Received {self.signals[signum]} signal")
        log.debug("Finishing current work before terminating")
        self.termination = True
