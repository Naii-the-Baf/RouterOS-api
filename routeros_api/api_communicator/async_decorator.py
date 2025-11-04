from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from routeros_api.api_communicator.exception_decorator import ExceptionAwareApiCommunicator


class AsyncApiCommunicator(object):
    def __init__(self, inner: ExceptionAwareApiCommunicator):
        self.inner = inner

    def call(self, *args, **kwargs) -> ResponsePromise:
        tag = self.inner.send(*args, **kwargs)
        return ResponsePromise(self.inner, tag)


class ResponsePromise(object):
    def __init__(self, receiver: ExceptionAwareApiCommunicator, tag):
        self.receiver = receiver
        self.tag = tag
        self.response = None

    def get(self):
        if self.response is None:
            self.response = self.receiver.receive(self.tag)
        return self.response

    def __iter__(self):
        return self.receiver.receive_iterator(self.tag)
