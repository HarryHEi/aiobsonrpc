# -*- coding: utf-8 -*-

"""
Decorators for proving services.
"""


def service_class(cls):
    """
    A class decorator enabling the instances of the class to be used
    as a ``services``-provider in `JSONRpc Objects`_
    and `BSONRpc Objects`_.

    Use decorators ``request``, ``notification``, ``rpc_request`` and
    ``rpc_notification`` to expose methods for the RPC peer node.
    """
    cls._request_handlers = {}
    cls._notification_handlers = {}
    for name, method in cls.__dict__.items():
        if hasattr(method, '_request_handler'):
            cls._request_handlers[name] = method
        if hasattr(method, '_notification_handler'):
            cls._notification_handlers[name] = method
    return cls


def aio_rpc_request(method):
    """
    A method decorator announcing the method to be exposed as
    a request handler.

    This decorator assumes that the first parameter (after ``self``)
    takes a BSONRpc/JSONRpc object reference as an argument, so that the method
    will have an access to make RPC callbacks on the peer node (requests and
    notifications) during its execution. From the second parameter onward the
    parameters are exposed as-is to the peer node.
    """
    method._request_handler = True
    return method


def aio_rpc_notification(method):
    """
    A method decorator announcing the method to be exposed as
    a notification handler.

    This decorator assumes that the first parameter (after ``self``)
    takes a BSONRpc/JSONRpc object reference as an argument.
    From the second parameter onward the
    parameters are exposed as-is to the peer node.
    """
    method._notification_handler = True
    return method
