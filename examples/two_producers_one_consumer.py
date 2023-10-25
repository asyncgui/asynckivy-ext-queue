import string
from kivy.app import App
import asynckivy as ak
from asynckivy_ext.queue import Queue


async def main():
    async def producer(name, q, items):
        for c in items:
            await q.put(c)
            print(name, "produced", c)
            await ak.sleep(.12)

    async def producers(*producers):
        await ak.wait_all(*producers)
        q.close()

    async def consumer(name, q):
        async for c in q:
            print(name, "consumed", c)
            await ak.sleep(.08)

    q = Queue(capacity=None)
    await ak.wait_all(
        producers(
            producer('P1', q, string.ascii_lowercase),
            producer('P2', q, string.ascii_uppercase),
        ),
        consumer('C ', q),
    )
    print('Done all tasks')
    App.get_running_app().stop()


if __name__ == "__main__":
    main_task = ak.start(main())
    App().run()
