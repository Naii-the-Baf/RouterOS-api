from typing import TYPE_CHECKING

from routeros_api.api_communicator.async_decorator import AsyncApiCommunicator
from routeros_api.api_communicator.base import ApiCommunicatorBase
from routeros_api.api_communicator.encoding_decorator import EncodingApiCommunicator
from routeros_api.api_communicator.exception_decorator import ExceptionAwareApiCommunicator
from routeros_api.api_communicator.key_cleaner_decorator import KeyCleanerApiCommunicator

if TYPE_CHECKING:
    from routeros_api.api import CloseConnectionExceptionHandler
    from routeros_api.base_api import Connection
    from routeros_api.communication_exception_parsers import ExceptionHandler


class ApiCommunicator(EncodingApiCommunicator):
    def __init__(self, base_api: Connection):
        communicator = ApiCommunicatorBase(base_api)

        key_cleaner_communicator = KeyCleanerApiCommunicator(communicator)

        self.exception_aware_communicator = ExceptionAwareApiCommunicator(key_cleaner_communicator)

        async_communicator = AsyncApiCommunicator(self.exception_aware_communicator)

        super(ApiCommunicator, self).__init__(async_communicator)

    def add_exception_handler(self, exception_handler: CloseConnectionExceptionHandler | ExceptionHandler) -> None:
        self.exception_aware_communicator.add_handler(exception_handler)
