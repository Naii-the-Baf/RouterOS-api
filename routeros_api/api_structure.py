import abc
import datetime
import ipaddress
import re

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class Field(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_mikrotik_value(self, arg: Any) -> bytes:
        """
        :rtype: bytes
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_python_value(self, bytes: bytes) -> Any:
        """
        :rtype bytes: bytes
        """
        raise NotImplementedError()


class StringField(Field):
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding

    def get_mikrotik_value(self, string: str) -> bytes:
        return string.encode(encoding=self.encoding, errors='backslashreplace')

    def get_python_value(self, bytes: bytes) -> str:
        return bytes.decode(encoding=self.encoding, errors='backslashreplace')


class BytesField(Field):
    def get_mikrotik_value(self, bytes: bytes) -> bytes:
        return bytes

    def get_python_value(self, bytes: bytes) -> bytes:
        return bytes


class BooleanField(Field):
    def get_mikrotik_value(self, condition: bool) -> bytes:
        return b'yes' if condition else b'no'

    def get_python_value(self, bytes: bytes) -> bool:
        assert bytes in (b'yes', b'true', b'no', b'false')
        return bytes in (b'yes', b'true')


class IntegerField(Field):
    def get_mikrotik_value(self, number: int) -> bytes:
        return str(number).encode()

    def get_python_value(self, bytes: bytes) -> int:
        return int(bytes.decode())


class TimedeltaField(Field):
    def get_mikrotik_value(self, timedelta: datetime.timedelta) -> bytes:
        if timedelta is None:
            return b'none'
        else:
            seconds = int(timedelta.total_seconds())
            return '{}s'.format(seconds).encode()

    def get_python_value(self, bytes: bytes) -> datetime.timedelta | None:
        if bytes == b'none':
            return None
        else:
            return self.parse_mikrotik_timedelta(bytes.decode())

    def parse_mikrotik_timedelta(self, time_string: str) -> datetime.timedelta:
        new_timedelta_format = (
            r'^((?P<weeks>\d+)w)?((?P<days>\d+)d)?'
            r'((?P<hours>\d+)h)?((?P<minutes>\d+)m)?((?P<seconds>\d+)s)?'
            r'((?P<milliseconds>\d+)ms)?$')
        old_timedelta_format = (
            r'^((?P<weeks>\d+)w)?((?P<days>\d+)d)?'
            r'(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+)'
            r'(\.(?P<milliseconds>\d+))?$')

        match = re.match(new_timedelta_format, time_string)
        if not match:
            match = re.match(old_timedelta_format, time_string)
        if match:
            groups = dict((k, int(v)) for k, v in match.groupdict('0').items())
            return datetime.timedelta(**groups)
        else:
            raise ValueError('{} does not match any mikrotik uptime format'
                             .format(time_string))


class IpNetworkField(Field):
    def get_mikrotik_value(self, ip_network: ipaddress.IPv4Network | ipaddress.IPv6Network) -> bytes:
        if ip_network:
            return str(ip_network).encode()
        else:
            return b''

    def get_python_value(self, bytes: bytes) -> ipaddress.IPv4Network | ipaddress.IPv6Network | None:
        if bytes:
            return ipaddress.ip_network(bytes.decode())
        else:
            return None


class ListField(Field):
    def __init__(self, subfield: Field):
        self.subfield = subfield

    def get_mikrotik_value(self, objects: list[Field]) -> bytes:
        return b','.join(
            self.subfield.get_mikrotik_value(obj) for obj in objects)

    def get_python_value(self, bytes: bytes) -> list[Field]:
        separator = b',' if b';' not in bytes else b';'
        return [
            self.subfield.get_python_value(serialized)
            for serialized in bytes.split(separator)]


default_structure: defaultdict[Any, StringField] = defaultdict(StringField)
