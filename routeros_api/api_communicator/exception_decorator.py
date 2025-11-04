from typing import TYPE_CHECKING

from routeros_api import exceptions

if TYPE_CHECKING:
    from routeros_api.api import CloseConnectionExceptionHandler
    from routeros_api.api_communicator.key_cleaner_decorator import KeyCleanerApiCommunicator
    from routeros_api.communication_exception_parsers import ExceptionHandler


class ExceptionAwareApiCommunicator(object):
    def __init__(self, inner: KeyCleanerApiCommunicator):
        self.inner: KeyCleanerApiCommunicator = inner
        self.exception_handlers: list[CloseConnectionExceptionHandler | ExceptionHandler] = []

    def send(self, *args, **kwargs):
        try:
            return self.inner.send(*args, **kwargs)
        except exceptions.RouterOsApiError as e:
            self.handle_exception(e)

    def receive(self, tag):
        try:
            return self.inner.receive(tag)
        except exceptions.RouterOsApiError as e:
            self.handle_exception(e)

    def receive_iterator(self, tag):
        try:
            for line in self.inner.receive_iterator(tag):
                yield line
        except exceptions.RouterOsApiError as e:
            self.handle_exception(e)

    def add_handler(self, handler: CloseConnectionExceptionHandler | ExceptionHandler):
        self.exception_handlers.append(handler)

    def handle_exception(self, exception):
        for subhandler in self.exception_handlers:
            try:
                subhandler.handle(exception)
            except exceptions.RouterOsApiError as e:
                exception = e
        raise exception
