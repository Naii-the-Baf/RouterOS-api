class RouterOsApiError(Exception):
    pass


class RouterOsApiConnectionError(RouterOsApiError):
    pass


class FatalRouterOsApiError(RouterOsApiError):
    pass


class RouterOsApiParsingError(RouterOsApiError):
    pass


class RouterOsApiCommunicationError(RouterOsApiError):
    def __init__(self, message: str, original_message: bytes):
        super(RouterOsApiCommunicationError, self).__init__(message, original_message)
        self.original_message = original_message


class RouterOsApiFatalCommunicationError(RouterOsApiError):
    pass


class RouterOsApiConnectionClosedError(RouterOsApiConnectionError):
    pass
