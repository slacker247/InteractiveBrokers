import asyncio
from ib_insync import IB

async def test_connection():
    ib = IB()
    await ib.connectAsync('127.0.0.1', 7497, clientId=123)
    print("Connected:", ib.isConnected())
    ib.disconnect()

asyncio.run(test_connection())
