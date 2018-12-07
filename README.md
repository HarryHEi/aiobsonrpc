
A Python library for JSON-RPC 2.0

This is a Specialized version of [bsonrpc](https://github.com/seprich/py-bson-rpc)
---------

aiobsonrpc
---------
Support asyncio

### Install
```
pip install aiobsonrpc
```

Example
---------

### echo server
```python
import asyncio

import aiobsonrpc


@aiobsonrpc.service_class
class EchoService(object):
    @aiobsonrpc.aio_rpc_request
    async def echo(self, _, data):
        await asyncio.sleep(1)
        print(data)
        return data


@asyncio.coroutine
async def on_connected(reader, writer):
    aiobsonrpc.JSONRpc(reader, writer, services=EchoService())


loop = asyncio.get_event_loop()

server = asyncio.start_server(on_connected, '0.0.0.0', 6789, loop=loop)
loop.create_task(server)

loop.run_forever()
```

### echo client
```python
import asyncio

import aiobsonrpc


@asyncio.coroutine
async def do_connect():
    reader, writer = await asyncio.open_connection('localhost', 6789, loop=loop)
    rpc = aiobsonrpc.JSONRpc(reader, writer)
    peer = rpc.get_peer_proxy(timeout=5)
    res = await peer.echo(123)
    print(res)

loop = asyncio.get_event_loop()
loop.run_until_complete(do_connect())

```
