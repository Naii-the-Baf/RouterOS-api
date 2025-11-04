from __future__ import annotations

import socket
import ssl

from routeros_api import exceptions

try:
    import errno
except ImportError:
    errno = None  # type: ignore

EINTR = getattr(errno, 'EINTR', 4)


def get_socket(hostname: str,
               port: int,
               use_ssl: bool = False,
               ssl_verify: bool = True,
               ssl_verify_hostname: bool = True,
               ssl_context: ssl.SSLContext | None = None,
               timeout: float = 15.0) -> SocketWrapper:
    while True:
        try:
            api_socket = socket.create_connection((hostname, port), timeout=timeout)
        except socket.error as e:
            if e.args[0] != EINTR:
                raise exceptions.RouterOsApiConnectionError(e)
        else:
            break
    set_keepalive(api_socket, after_idle_sec=10)
    # A provided ssl_context overrides any options
    if ssl_context is None and use_ssl:
        ssl_context = ssl.create_default_context()
        if ssl_verify:
            ssl_context.check_hostname = ssl_verify_hostname
            ssl_context.verify_mode = ssl.CERT_REQUIRED
        else:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
    if ssl_context is not None:
        api_socket = ssl_context.wrap_socket(api_socket, server_hostname=hostname)
    return SocketWrapper(api_socket)


# http://stackoverflow.com/a/14855726
def set_keepalive(sock, after_idle_sec=1, interval_sec=3, max_fails=5):
    """Set TCP keepalive on an open socket.

    It activates after 1 second (after_idle_sec) of idleness,
    then sends a keepalive ping once every 3 seconds (interval_sec),
    and closes the connection after 5 failed ping (max_fails), or 15 seconds
    """
    if hasattr(socket, "SO_KEEPALIVE"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    if hasattr(socket, "TCP_KEEPIDLE"):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
    if hasattr(socket, "TCP_KEEPINTVL"):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
    if hasattr(socket, "TCP_KEEPCNT"):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)


class Socket(object):
    def send(self, bytes):
        raise NotImplementedError

    def receive(self, length):
        raise NotImplementedError

    def _receive_and_check_connection(self, length):
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def settimeout(self, timeout: float) -> None:
        raise NotImplementedError


class DummySocket(Socket):
    def close(self) -> None:
        pass

    def settimeout(self, timeout: float) -> None:
        pass


class SocketWrapper(Socket):
    def __init__(self, socket: socket.socket):
        self.socket = socket

    def send(self, bytes):
        return self.socket.sendall(bytes)

    def receive(self, length):
        while True:
            try:
                return self._receive_and_check_connection(length)
            except socket.error as e:
                if e.args[0] == EINTR:
                    continue
                else:
                    raise

    def _receive_and_check_connection(self, length):
        bytes = self.socket.recv(length)
        if bytes:
            return bytes
        else:
            raise exceptions.RouterOsApiConnectionClosedError

    def close(self) -> None:
        return self.socket.close()

    def settimeout(self, timeout: float):
        self.socket.settimeout(timeout)
