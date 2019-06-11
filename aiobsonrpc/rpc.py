# -*- coding: utf-8 -*-
"""
Main module providing BSONRpc and JSONRpc.
"""

import re
import asyncio

from .definitions import Definitions, RpcErrors
from .exceptions import ResponseTimeout
from .options import DefaultOptionsMixin
from .socket_queue import SocketQueue
from .util import PeerProxy
from .log import logger


# 请求标识 => { 事件(event)， 返回值(value)， 异常(exception) }
id_to_request = {}


class RpcBase(DefaultOptionsMixin):
    """RPC 基类"""
    def __init__(self, reader, writer, *, loop=None, services=None, protocol='jsonrpc', protocol_version='2.0'):
        """
        :param reader: StreamReader
        :param writer: StreamWriter
        :param loop: event loop
        :param services: @server_class
        :param protocol: default jsonrpc
        :param protocol_version: default 2.0
        """
        assert (hasattr(services, '_request_handlers') and
                hasattr(services, '_notification_handlers'))
        if not loop:
            loop = asyncio.get_event_loop()
        self.peer_name = writer.get_extra_info('socket').getpeername()
        self.loop = loop
        self.definitions = Definitions(protocol, protocol_version)
        self.services = services
        self.socket_queue = SocketQueue(reader, writer, loop)
        loop.create_task(self._handle_loop())

    @asyncio.coroutine
    async def _handle_execute(self, msg):
        """
        执行远程调用，回复响应
        :param msg: dict
        """
        if 'id' in msg:
            response = await self._execute_request(msg)
            await self.socket_queue.put(response)
        else:
            await self._execute_notification(msg)

    @asyncio.coroutine
    async def _handle_loop(self):
        """
        循环处理收到的JSON RPC字典数据，排定客户端调用方法到事件队列。
        """
        while True:
            msg = await self.socket_queue.get()
            try:
                if not msg or not isinstance(msg, dict):
                    self.socket_queue.close()
                    break
                if 'result' in msg or 'error' in msg:
                    self._handle_response(msg)
                    continue
                self.loop.create_task(self._handle_execute(msg))
            except Exception as e:
                logger.error('{}'.format(str(e)))

    @staticmethod
    def _handle_response(msg):
        """
        处理收到的响应，设置事件标识。
        :param msg: dict
        """
        msg_id = msg['id']
        if msg_id in id_to_request:
            id_to_request[msg_id]['event'].set()
            if 'result' in msg:
                id_to_request[msg_id]['value'] = msg['result']
            elif 'error' in msg:
                id_to_request[msg_id]['exception'] = msg['error']

    @staticmethod
    def _get_params(msg):
        """
        按格式返回 msg 中的 params
        :param msg: dict
        """
        if 'params' not in msg:
            return [], {}
        params = msg['params']
        if isinstance(params, list):
            return params, {}
        if isinstance(params, dict):
            return [], params
        return [params], {}

    @asyncio.coroutine
    async def _execute_request(self, msg):
        """
        执行来自客户端的远程调用
        :param msg: dict
        :return: ok_response or error_response, dict
        """
        msg_id = msg['id']
        method_name = msg['method']
        args, kwargs = self._get_params(msg)
        try:
            method = self.services._request_handlers.get(method_name)
            if method:
                result = await method(self.services, self, *args, **kwargs)
                return self.definitions.ok_response(msg_id, result)
            else:
                return self.definitions.error_response(
                    msg_id, RpcErrors.method_not_found)
        except Exception as e:
            return self.definitions.error_response(
                msg_id, RpcErrors.server_error, str(e))

    @asyncio.coroutine
    async def _execute_notification(self, msg):
        """
        执行来自客户端的通知
        :param msg: dict
        """
        method_name = msg['method']
        args, kwargs = self._get_params(msg)
        method = self.services._notification_handlers.get(method_name)
        if method:
            try:
                await method(self.services, self, *args, **kwargs)
            except Exception as e:
                logger.error('_execute_notification {}'.format(e))
        else:
            logger.error('_execute_notification Unrecognized notification from peer: {}'.format(str(msg)))

    @property
    def is_closed(self):
        """
        :property: bool -- Closed by peer node or with ``close()``
        """
        return self.socket_queue.is_closed

    @asyncio.coroutine
    async def invoke_request(self, method_name, *args, **kwargs):
        """
        Invoke RPC Request.

        :param method_name: Name of the request method.
        :type method_name: str
        :param args: Arguments
        :param kwargs: Keyword Arguments.
        :returns: Response value(s) from peer.
        :raises: JsonRpcError

        A timeout for the request can be set by giving a special keyword
        argument ``timeout`` (float value of seconds) which can be prefixed
        by any number of underscores - if necessary - to differentiate it from
        the actual keyword arguments going to the peer node method call.

        e.g.
        ``invoke_request('testing', [], {'_timeout': 22, '__timeout: 10.0})``
        would call a request method ``testing(_timeout=22)`` on the RPC peer
        and wait for the response for 10 seconds.

        **NOTE:**
          Use either arguments or keyword arguments. Both can't
          be used in a single call.
          (Naturally the timeout argument does not count to the rule.)
        """
        rec = re.compile(r'^_*timeout$')
        to_keys = sorted(filter(lambda x: rec.match(x), kwargs.keys()))
        if to_keys:
            timeout = kwargs[to_keys[0]]
            del kwargs[to_keys[0]]
        else:
            timeout = None
        msg_id = next(self.id_generator)
        try:
            request = self.definitions.request(msg_id, method_name, args, kwargs)
            await self.socket_queue.put(
                request,
                timeout=timeout
            )
            request_event = asyncio.Event()
            id_to_request[msg_id] = dict(
                event=request_event,
                value=None,
                exception=None
            )
            wait_cor = request_event.wait()
            await asyncio.wait([wait_cor], timeout=timeout)
            if not request_event.is_set():
                del id_to_request[msg_id]
                raise ResponseTimeout(u'Waiting response expired.')
            result = id_to_request[msg_id]['value']
            exception = id_to_request[msg_id]['exception']
            if exception:
                logger.error('method: {}, args: {}, kwargs: {}, {}'.format(
                    method_name, args, kwargs, exception['message']
                ))
                error = RpcErrors.error_to_exception(exception)
                raise error
            del id_to_request[msg_id]
            return result
        except Exception as e:
            raise e

    @asyncio.coroutine
    async def invoke_notification(self, method_name, *args, **kwargs):
        """
        Send an RPC Notification.

        :param method_name: Name of the notification method.
        :type method_name: str
        :param args: Arguments
        :param kwargs: Keyword Arguments.

        **NOTE:**
          Use either arguments or keyword arguments. Both can't
          be used simultaneously in a single call.
        """
        # self.socket_queue.put(
        #     self.definitions.notification(method_name, args, kwargs))

        request = self.definitions.notification(method_name, args, kwargs)
        await self.socket_queue.put(request)

    def get_peer_proxy(self, requests=None, notifications=None, timeout=None):
        """
        Get a RPC peer proxy object. Method calls to this object
        are delegated and executed on the connected RPC peer.

        :param requests: A list of method names which can be called and
                         will be delegated to peer node as requests.
                         Default: None -> All arbitrary attributes are
                         handled as requests to the peer.
        :type requests: list of str | None
        :param notifications: A list of method names which can be called and
                              will be delegated to peer node as notifications.
                              Default: None -> If ``requests`` is not ``None``
                              all other attributes are handled as
                              notifications.
        :type notifications: list of str | None
        :param timeout: Timeout in seconds, maximum time to wait responses
                        to each Request.
        :type timeout: float | None
        :returns: A proxy object. Attribute method calls delegated over RPC.

        ``get_peer_proxy()`` (without arguments) will return a proxy
        where all attribute method calls are turned into Requests,
        except calls via ``.n`` which are turned into Notifications.
        Example:
        ::

          proxy = rpc.get_peer_proxy()
          proxy.n.log_this('hello')          # -> Notification
          result = proxy.swap_this('Alise')  # -> Request

        But if arguments are given then the interpretation is explicit and
        ``.n``-delegator is not used:
        ::

          proxy = rpc.get_peer_proxy(['swap_this'], ['log_this'])
          proxy.log_this('hello')            # -> Notification
          result = proxy.swap_this('esilA')  # -> Request
        """
        return PeerProxy(self, requests, notifications, timeout)

    def close(self):
        """
        Close the connection and stop the internal dispatcher.
        """
        # Closing the socket queue causes the dispatcher to close also.
        self.socket_queue.close()

    async def join(self):
        await self.socket_queue.join()


class DefaultServices(object):
    """
    创建JSON RPC对象时的缺省services
    """

    _request_handlers = {}

    _notification_handlers = {}


class JSONRpc(RpcBase):
    """
    JSON RPC Connector. Implements the `JSON-RPC 2.0`_ specification.

    Connects via socket to RPC peer node. Provides access to the services
    provided by the peer node. Optional ``services`` parameter will take an
    object of which methods are accessible to the peer node.

    Various methods of JSON message framing are available for the stream
    transport.

    .. _`JSON-RPC 2.0`: http://www.jsonrpc.org/specification
    """

    #: Protocol name used in messages
    protocol = 'jsonrpc'

    #: Protocol version used in messages
    protocol_version = '2.0'

    def __init__(self, reader, writer, *, loop=None, services=None):
        """
        :param reader: StreamReader
        :param writer: StreamWriter
        :param loop: event loop
        :param services: @server_class
        """
        if not services:
            services = DefaultServices()
        if not loop:
            loop = asyncio.get_event_loop()

        super(JSONRpc, self).__init__(
                reader,
                writer,
                loop=loop,
                services=services,
                protocol=self.protocol,
                protocol_version=self.protocol_version
        )
