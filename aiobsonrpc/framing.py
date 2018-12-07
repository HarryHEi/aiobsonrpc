# -*- coding: utf-8 -*-

from .exceptions import FramingError


class JSONFramingRFC7464(object):
    """
    RFC-7464 framing.
    """

    @classmethod
    def extract_message(cls, raw_bytes):
        if len(raw_bytes) < 2:
            return None, raw_bytes
        if raw_bytes[0] != 0x1e:
            raise FramingError(
                'Start marker is missing: %s' % raw_bytes)
        if b'\x0a' in raw_bytes:
            b_msg, rest = raw_bytes.split(b'\x0a', 1)
            return b_msg[1:], rest
        else:
            if b'\x1e' in raw_bytes[1:]:
                raise FramingError(
                    'End marker is missing: %s' % raw_bytes)
            return None, raw_bytes

    @classmethod
    def into_frame(cls, message_bytes):
        return b'\x1e' + message_bytes + b'\x0a'
