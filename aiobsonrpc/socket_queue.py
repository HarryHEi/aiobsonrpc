import asyncio.queues
import json

from .exceptions import (JsonRpcError, DecodingError)
from .framing import JSONFramingRFC7464


class SocketQueue(object):
    def __init__(self, reader, writer, loop=None):
        """
        :param reader: StreamReader
        :param writer: StreamWriter
        :param loop: event loop
        """

        if not loop:
            loop = asyncio.get_event_loop()

        self._reader = reader
        self._writer = writer
        self._queue = asyncio.queues.Queue()
        self._closed = False

        self._receive_task = loop.create_task(self._receive())

    @asyncio.coroutine
    async def _to_queue(self, buffer):
        """
        输入数据流，解析出json rpc对象，放到queue
        :param buffer: bytes
        :return: 返回剩余bytes
        """

        b_msg, buffer = JSONFramingRFC7464.extract_message(buffer)
        while b_msg is not None:
            await self._queue.put(json.loads(b_msg))
            b_msg, buffer = JSONFramingRFC7464.extract_message(buffer)
        return buffer

    @asyncio.coroutine
    async def _receive(self):
        """循环读"""

        buffer = b''
        while True:
            try:
                chunk = await self._reader.read(1024)
                buffer = await self._to_queue(buffer + chunk)
                if chunk == b'':
                    break
            except DecodingError as e:
                await self._queue.put(e)
            except Exception as e:
                await self._queue.put(e)
                break
        await self._queue.put(None)
        self._closed = True
        self._writer.close()

    @asyncio.coroutine
    async def put(self, data, timeout=None):
        """
        向socket写消息
        :param data: dict
        :param timeout: 超时时间
        """
        if self._closed:
            raise JsonRpcError('Attempt to put items to closed queue.')
        self._writer.write(JSONFramingRFC7464.into_frame(json.dumps(data).encode()))
        write_cor = self._writer.drain()
        await asyncio.wait([write_cor], timeout=timeout)

    @asyncio.coroutine
    async def get(self):
        """
        从队列获取一条消息
        :return: dict
        """
        return await self._queue.get()
    
    @property
    def is_closed(self):
        """
        :property: bool -- Closed by peer node or with ``close()``
        """
        return self._closed

    def close(self):
        self._closed = True
        self._writer.close()

    async def join(self):
        await self._receive_task
