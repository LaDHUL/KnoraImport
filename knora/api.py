import requests
import json
import logging
import collections
import time

import sys

"""
    
    Knora API Wrapper
    
    for import
    
"""

ExceptionType = collections.namedtuple('ExceptionType', ['Login', 'Wrong'])

ThumbnailArgs = collections.namedtuple('ThumbnailArg', ['file', 'type', 'filename', 'sipi_filename'])

class KnoraException(Exception):
    """
    Exceptions thrown by this API
    """
    def __init__(self, type: ExceptionType, comment: str):
        self.type = type
        self.comment = comment


class Knora():
    """

    """
    def __init__(self, knora_url, sipi_url):
        self.api_url = knora_url
        self.sipi_url = sipi_url
        # session
        self.session = None
        self.cookie = None
        self.user = None
        self.pwd = None
        self.sipi_sid = None
        self.isDryRun = False
        self.knoraSession = None
        self.sipiSession = None
        self.useSipiSession = False
        # logger
        self.logger = logging.getLogger(__name__)
        # execution stats
        self.knoraTimings = ExecStats("knora")
        self.sipiTimings = ExecStats("sipi")

    def dryRun(self):
        """
        set the dry run option; no actual request will be passed to Knora/Sipi
        Returns:
            nothing
        """
        self.isDryRun = True

    def setSipiSession(self):
        """
        keep and reuse a session for sipi
        Returns:
            nothing
        """
        self.useSipiSession = True

    def login(self, user: str, pwd: str):
        """
        log into Knora and Sipi
        Args:
            user:
            pwd:

        Returns:
            nothing
        """
        self.logger.info(self.sipiTimings.logStart())

        # dry run shortcut
        if self.isDryRun:
            return

        # login knora
        try:
            self.knoraSession = requests.Session()
            r = self.knoraSession.post(self.api_url +'/v1/session', auth=(user, pwd))
            r.raise_for_status()
            self.session = r.headers['Set-Cookie']
            self.cookie = r.cookies
            self.user = user
            self.pwd = pwd

        except requests.HTTPError as e:
            # TODO: explicit the error
            logging.debug("exception: %s", e)
            self.user = None
            self.pwd = None
            raise KnoraException(ExceptionType.Login, "Knora login failed")

        # login sipi
        try:
            sid = self.session.partition('=')[2]
            self.sipi_sid = {'sid': sid}
            self.cookie.set('sid', sid)
            self.sipiSession = requests.Session()
            r2 = self.sipiSession.post(self.sipi_url + '/Knora_login', data=self.sipi_sid)
            r2.raise_for_status()

        except requests.HTTPError as e:
            # TODO: explicit the error
            logging.debug("exception: %s", e)
            raise KnoraException(ExceptionType.Login, "Sipi login failed")

    def create_resource(self, params):
        """
        This functions creates a new resource in SALSAH
        (POST to api/resources)

        Keyword arguments:
        params -- the parameters of the resource to create (dictionary)

        Returns:
        the SALSAH-ID of the new resource

        When an error occurs, None is returned
        """

        self.knoraTimings.start()

        if self.isDryRun:
            return "dryRun-" + str(time.time())

        self.logger.debug(json.dumps(params))
        try:
            #with self.knoraSession.post(self.api_url + '/v1/resources', headers={'content-type': 'application/json'}, data=json.dumps(params), auth=(self.user, self.pwd), cookies=self.cookie) as r:
            #    r.raise_for_status()
            #    return r.json().get('res_id')
            r = self.knoraSession.post(self.api_url + '/v1/resources', headers={'content-type': 'application/json'}, data=json.dumps(params), auth=(self.user, self.pwd), cookies=self.cookie)
            r.raise_for_status()
            self.knoraTimings.end()
            r.close
            return r.json().get('res_id')
        except Exception as e:
            self.logger.error('Creation of resource failed with HTTP %s\nParams: %s\nHTTP header: %s\nResponse Body: %s', e,
                         params, r.headers, r.text)
            return None

    def get(self, url: str):
        if self.isDryRun:
            return {}

        try:
            r = self.knoraSession.get(self.api_url + url, headers={'content-type': 'application/json'}, auth=(self.user, self.pwd), cookies=self.cookie)
            r.raise_for_status()
            self.knoraTimings.end()
            r.close
            return r.json()
        except Exception as e:
            self.logger.error('Creation of resource failed with HTTP %s\nParams: %s\nHTTP header: %s\nResponse Body: %s', e,
                         r.headers, r.text)
            return None


    def make_thumbnail(self, param: ThumbnailArgs):
        """
        Creates a sipi thumbnail, which means upload the file to sipi prior to knora knowing it
        Args:
            param: the arguments for creating a thumbnail

        Returns:
            the file name and urls for later declaring the file into knora
        """

        self.sipiTimings.start()

        if self.isDryRun:
            sipi_response = {'filename': "dryRun-" + str(time.time())}
            return sipi_response

        try:
            with open(param.file, 'rb') as f:
                files = {'file': (param.sipi_filename, f, param.type)}
                r2 = self.sipiSession.post(self.sipi_url + '/make_thumbnail', files=files, stream=False) if self.useSipiSession else requests.post(self.sipi_url + '/make_thumbnail', files=files, stream=False)
                if r2.ok:
                    self.logger.debug('sipi: uploaded: %s', param.file)
                else:
                    self.logger.error('sipi: failed to upload: %s / %s', param.file, param.filename)
                r2.raise_for_status()
                sipi_thumb = json.loads(r2.content.decode())
                self.sipiTimings.end()
                r2.close
                return sipi_thumb

        except requests.HTTPError as e:
            self.logger.debug("exception: ", e)
            raise KnoraException(ExceptionType.Login, "Sipi thumbnail failed")
        except Exception as e:
            self.logger.debug("exception: ", e)
            raise KnoraException(ExceptionType.Login, "Sipi thumbnail failed")

    def logTimings(self):
        self.logger.info(self.knoraTimings)
        self.logger.info(self.sipiTimings)


def create_params(restype_id):
    """
    This function creates the structure for the params sent
    to the SALSAH API

    Returns:
    A dictionary with the basic structure for the params

    params = {
        'restype_id': restype_id,
        'properties': {}
        }

    """

    params = {
        'restype_id': restype_id,
        'properties': {}
    }
    return params


class ExecStats:
    """
    Accounting for the execution time of multiple events
    """

    def __init__(self, name):
        self.t0 = time.localtime()
        self.events = 0
        self.total = 0
        self.min = sys.maxsize
        self.max = 0
        self.tstart = 0
        self.name = name

    def logStart(self):
        """
        Formats a start message
        Returns:
            start message to be logged
        """
        return self.name + ": " + time.strftime("%Y-%m-%d %H:%M:%S", self.t0)

    def start(self):
        """
        trigger the timer for one event
        Returns:
            nothing
        """
        self.tstart = time.time()

    def end(self):
        """
        release the timer after the event completion
        Returns:
            nothing
        """
        spend = time.time() - self.tstart
        self.total += spend
        if self.min > spend:
            self.min = spend
        if self.max < spend:
            self.max = spend
        self.events += 1

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        """
        Returns:
            formatted results of the events execution time
        """
        if self.events == 0:
            self.events = 1
        end = time.localtime()
        return "{} timings -- ran for {} s ({} - {})\n\tuploaded: {}, timings, avg: {}, min: {}, max: {}".format(
            self.name,
            time.mktime(end) - time.mktime(self.t0),
            self.logStart(), time.strftime("%Y-%m-%d %H:%M:%S", end),
            self.events, self.total / self.events, self.min, self.max)

