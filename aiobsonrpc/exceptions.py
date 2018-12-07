# -*- coding: utf-8 -*-


class JsonRpcError(RuntimeError):
    """
    Base class for produced errors.
    """


class CodecError(JsonRpcError):
    """
    Common base for framing and codec errors.
    """


class FramingError(CodecError):
    """
    Typically irrecoverable errors in message framing/unframing.
    """


class EncodingError(CodecError):
    """
    Error at encoding message.
    """


class DecodingError(CodecError):
    """
    Error while decoding message.
    """


class ResponseTimeout(JsonRpcError):
    """
    Response to Request(s) did not arrive in required time.
    """


class PeerError(JsonRpcError):
    """
    Base class for exceptions promoted from error responses.
    """

    def __init__(self, code, message, details):
        super(PeerError, self).__init__(
            u'Code: %s Message: %s Details: %s' %
            (str(code),
             str(message),
             str(details)))
        self.code = code
        self.message = message
        self.details = details


class UnspecifiedPeerError(PeerError):
    """
    Unspecified code
    """


class ParseError(PeerError):
    """
    Code -32700
    """


class InvalidRequest(PeerError):
    """
    Code -32600
    """


class MethodNotFound(PeerError):
    """
    Code -32601
    """


class InvalidParams(PeerError):
    """
    Code -32602
    """


class InternalError(PeerError):
    """
    Code -32603
    """


class ServerError(PeerError):
    """
    Code -32000
    """
