# aiobsonrpc

[bsonrpc](https://github.com/seprich/py-bson-rpc) for asyncio. 

Python 3.5+

## Getting Started

### Installing

```
pip install aiobsonrpc
```

### Example

Server

```python
import asyncio
import aiobsonrpc


@aiobsonrpc.service_class
class EchoService(object):
    @aiobsonrpc.aio_rpc_request
    async def echo(self, _, data):
        await asyncio.sleep(1)
        return data


async def on_connected(reader, writer):
    aiobsonrpc.JSONRpc(reader, writer, services=EchoService())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    
    server = asyncio.start_server(on_connected, '0.0.0.0', 6789, loop=loop)
    loop.create_task(server)
    
    loop.run_forever()
```

Client

```python
import asyncio
import aiobsonrpc


async def do_connect():
    reader, writer = await asyncio.open_connection('localhost', 6789, loop=loop)
    rpc = aiobsonrpc.JSONRpc(reader, writer)
    peer = rpc.get_peer_proxy(timeout=5)
    result = await peer.echo(123)
    print(result)  # 123

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(do_connect())
```
