=====
Usage
=====

.. code-block::

    from kivy.app import App
    import asynckivy as ak
    from asynckivy_ext.queue import Queue


    async def producer(q):
        for c in "ABC":
            await q.put(c)
            print('produced', c)
        q.half_close()


    async def consumer(q):
        async for c in q:
            print('consumed', c)


    q = Queue(capacity=1)
    ak.start(producer(q))
    ak.start(consumer(q))
    App().run()

.. code-block:: text

    produced A
    consumed A
    produced B
    consumed B
    produced C
    consumed C
