
from time import sleep

import requests

from nerus.utils import Record
from nerus.const import (
    LOCALHOST,
    ANNOTATORS_BASE_PORT
)
from nerus.markup import Markup
from nerus.docker import (
    start_container,
    remove_container,
    generate_name,
    generate_port
)


class AnnotatorError(Exception):
    pass


class AnnotatorMarkup(Markup):
    label = None


PUTIN = 'Путин'


class Annotator(Record):
    __attributes__ = ['host', 'port']

    name = None

    def __init__(self, host=None, port=None):
        if not host:
            host = self.host
        self.host = host
        if not port:
            port = self.port
        self.port = port

    def __call__(self, text):
        raise NotImplementedError

    def map(self, texts):
        for text in texts:
            yield self(text)

    @property
    def ready(self):
        try:
            self(PUTIN)
            return True
        except (requests.ConnectionError, requests.ReadTimeout):
            return False

    def wait(self, callback=None, retries=30, delay=2):
        for _ in range(retries):
            if self.ready:
                break
            else:
                if callback:
                    callback()
                sleep(delay)
        else:
            raise AnnotatorError('failed to start')


class ChunkAnnotator(Annotator):
    __attributes__ = ['host', 'port', 'chunk']

    def map(self, texts):
        raise NotImplementedError

    def __call__(self, text):
        return next(self.map([text]))


class ContainerAnnotator(Annotator):
    image = None
    container_port = None

    def __init__(self):
        super(ContainerAnnotator, self).__init__(LOCALHOST, port=None)
        self.container_name = None

    def __call__(self, texts):
        if not self.port:
            raise AnnotatorError('container not running')
        return super(ContainerAnnotator, self).__call__(texts)

    def start(self):
        self.container_name = generate_name(prefix=self.name)
        self.port = generate_port(start=ANNOTATORS_BASE_PORT)
        start_container(
            self.image,
            self.container_name,
            self.container_port,
            self.port
        )

    def stop(self):
        remove_container(self.container_name)
        self.container_name = None
        self.port = None
