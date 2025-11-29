from db import engine
import asyncio

async def test():
    async with engine.begin() as conn:
        print("Connected OK")
