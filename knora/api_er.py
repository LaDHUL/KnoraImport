import logging
import time

from knora.api import Knora, ThumbnailArgs, KnoraException


class Knora_ER(Knora):
    """
    Knora API Wrapper with attempt to recover error (Knora Error Recovery)
    """

    def __init__(self, knora_url, sipi_url, attempts=10, timeout=5):
        self.attempts = attempts
        self.timeout = timeout
        super().__init__(knora_url, sipi_url)
        self.logger = logging.getLogger(__name__)

    def login(self, user: str, pwd: str):
        lookover = super().login
        args = [user, pwd]
        return self.retry(lookover, args)

    def create_resource(self, param: dict):
        lookover = super().create_resource
        args = [param]
        return self.retry(lookover, args)

    def make_thumbnail(self, param: ThumbnailArgs):
        lookover = super().make_thumbnail
        args = [param]
        return self.retry(lookover, args)

    def get(self, url: str):
        lookover = super().get
        args = [url]
        return self.retry(lookover, args)

    def retry(self, lookover, args):
        for attempt in range(1, self.attempts):
            try:
                return lookover(*args)
            except KnoraException as e:
                self.logger.info("attempt %s/%s: caught exception: %s", attempt, self.attempts, e)
                if attempt == self.attempts:
                    raise e
                else:
                    time.sleep(attempt)
