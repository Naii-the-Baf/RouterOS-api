from __future__ import annotations

import logging

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from routeros_api.api_communicator.async_decorator import AsyncApiCommunicator
    from routeros_api.api_communicator.async_decorator import ResponsePromise

logger = logging.getLogger(__name__)


class EncodingApiCommunicator(object):
    def __init__(self, inner: AsyncApiCommunicator):
        self.inner = inner

    def call(self,
             path: str,
             command: str,
             arguments: dict[str, bytes | None] | None = None,
             queries: dict[str, bytes | None] | None = None,
             additional_queries: tuple = ()):
        path_bytes = path.encode()
        command_bytes = command.encode()
        arguments = self.transform_dictionary(arguments or {})
        queries = self.transform_dictionary(queries or {})
        promise = self.inner.call(
            path_bytes, command_bytes, arguments, queries, additional_queries)
        return self.decorate_promise(promise)

    def transform_dictionary(self, dictionary):
        return dict(self.transform_item(item) for item in dictionary.items())

    def transform_item(self, item):
        key, value = item
        if value is not None and not isinstance(value, bytes):
            logger.warning(
                'Non-bytes value passed as item value ({}). You should probably use api.get_resource() instead of '
                'api.get_binary_resource() or encode arguments yourself.'.format(value))
            value = value.encode()
        return (key.encode(), value)

    def decorate_promise(self, promise: ResponsePromise) -> EncodedPromiseDecorator:
        return EncodedPromiseDecorator(promise)


class EncodedPromiseDecorator(object):
    def __init__(self, inner: ResponsePromise):
        self.inner = inner

    def get(self):
        response = self.inner.get()
        return response.map(self.transform_row)

    def __iter__(self):
        return map(self.transform_row, self.inner)

    def transform_row(self, row):
        return dict(self.transform_item(item) for item in row.items())

    def transform_item(self, item):
        key, value = item
        return (key.decode(), value)
