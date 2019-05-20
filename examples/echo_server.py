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
