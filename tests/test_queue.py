import pytest
p = pytest.mark.parametrize
p_order = p('order', ('lifo', 'fifo', 'small-first'))
p_capacity = p('capacity', [1, 2, None, ])
p_capacity2 = p('capacity', [1, 2, 3, 4, None, ])
p_limited_capacity = p('capacity', [1, 2, ])


@pytest.fixture(autouse=True)
def autouse_kivy_clock(kivy_clock):
    pass


@p('capacity', (-1, 0, 0.0, 1.0, -1.0, '1', ))
def test_invalid_capacity_value(capacity):
    from asynckivy_ext.queue import Queue
    with pytest.raises(ValueError):
        Queue(capacity=capacity)


@p_capacity
@p_order
def test_container_type(capacity, order):
    from asynckivy_ext.queue import Queue
    q = Queue(capacity=capacity, order=order)
    if capacity != 1 and order == 'fifo':
        from collections import deque
        assert isinstance(q._c, deque)
    else:
        assert isinstance(q._c, list)


@p_capacity
@p('close', [True, False, ])
@p('nowait', [True, False, ])
def test_put_to_closed_queue(capacity, close, nowait):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue, Closed
    q = Queue(capacity=capacity)
    q.close() if close else q.half_close()
    with pytest.raises(Closed):
        q.put_nowait('Z') if nowait else ak.start(q.put('Z'))


@p_capacity
@p('close', [True, False, ])
@p('nowait', [True, False, ])
def test_get_to_closed_queue(capacity, close, nowait):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue, Closed
    q = Queue(capacity=capacity)
    q.close() if close else q.half_close()
    with pytest.raises(Closed):
        q.get_nowait() if nowait else ak.start(q.get())


@p_capacity2
@p('close', [True, False, ])
def test_async_for(kivy_clock, capacity, close):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue

    async def producer(q, items):
        for i in items:
            await q.put(i)

    async def consumer(q):
        return ''.join([item async for item in q])

    q = Queue(capacity=capacity)
    p = ak.start(producer(q, 'ABC'))
    c = ak.start(consumer(q))
    assert not p.finished
    assert not c.finished
    kivy_clock.tick()
    assert p.finished
    assert not c.finished
    q.close() if close else q.half_close()
    assert c.result == 'ABC'


@p_capacity2
def test_one_producer_and_two_consumers(kivy_clock, capacity):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue

    async def producer(q):
        for c in 'A1B2C3':
            await q.put(c)
        q.half_close()

    async def consumer(q):
        return ''.join([item async for item in q])

    q = Queue(capacity=capacity)
    p = ak.start(producer(q))
    c1 = ak.start(consumer(q))
    c2 = ak.start(consumer(q))
    assert not p.finished
    assert not c1.finished
    assert not c2.finished
    kivy_clock.tick()
    assert p.finished
    assert c1.result == 'ABC'
    assert c2.result == '123'


@p_capacity2
@p('close', [True, False, ])
def test_two_producers_and_one_consumer(kivy_clock, capacity, close):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue

    async def producer(q, items):
        for i in items:
            await q.put(i)

    async def consumer(q):
        return ''.join([item async for item in q])

    q = Queue(capacity=capacity)
    p1 = ak.start(producer(q, 'ABC'))
    p2 = ak.start(producer(q, '123'))
    c = ak.start(consumer(q))
    assert not p1.finished
    assert not p2.finished
    assert not c.finished
    kivy_clock.tick()
    assert p1.finished
    assert p2.finished
    assert not c.finished
    q.close() if close else q.half_close()
    assert c.result == 'A1B2C3'


@p_capacity2
@p('close', [True, False, ])
def test_two_producers_and_two_consumers(kivy_clock, capacity, close):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue

    async def producer(q, items):
        for i in items:
            await q.put(i)

    async def consumer(q):
        return ''.join([item async for item in q])

    q = Queue(capacity=capacity)
    p1 = ak.start(producer(q, 'ABC'))
    p2 = ak.start(producer(q, '123'))
    c1 = ak.start(consumer(q))
    c2 = ak.start(consumer(q))
    assert not p1.finished
    assert not p2.finished
    assert not c1.finished
    assert not c2.finished
    kivy_clock.tick()
    assert p1.finished
    assert p2.finished
    assert not c1.finished
    assert not c2.finished
    q.close() if close else q.half_close()
    assert c1.result == 'ABC'
    assert c2.result == '123'


@p('n_producers', range(3))
@p('n_consumers', range(3))
@p('close', [True, False, ])
@p_capacity2
def test_close_a_queue_while_it_holding_putters_and_getters(n_producers, n_consumers, close, capacity):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue, Closed

    async def producer(q):
        with pytest.raises(Closed):
            await q.put(None)
    async def consumer(q):
        with pytest.raises(Closed):
            await q.get()

    q = Queue(capacity=capacity)
    producers = [ak.start(producer(q)) for __ in range(n_producers)]
    consumers = [ak.start(consumer(q)) for __ in range(n_consumers)]
    for p in producers:
        assert not p.finished
    for c in consumers:
        assert not c.finished
    q.close() if close else q.half_close()
    for p in producers:
        assert p.finished
    for c in consumers:
        assert c.finished


@p_order
def test_various_statistics(kivy_clock, order):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue
    q = Queue(capacity=2, order=order)
    assert q.order == order
    assert len(q) == 0
    assert q.capacity == 2
    assert q.size == 0
    assert q.is_empty
    assert not q.is_full
    ak.start(q.put(1))
    assert q.size == 0
    assert q.is_empty
    assert not q.is_full
    kivy_clock.tick()
    assert q.size == 1
    assert not q.is_empty
    assert not q.is_full
    ak.start(q.put(2))
    assert q.size == 1
    assert not q.is_empty
    assert not q.is_full
    kivy_clock.tick()
    assert q.size == 2
    assert not q.is_empty
    assert q.is_full
    ak.start(q.get())
    assert q.size == 2
    assert not q.is_empty
    assert q.is_full
    kivy_clock.tick()
    assert q.size == 1
    assert not q.is_empty
    assert not q.is_full
    ak.start(q.get())
    assert q.size == 1
    assert not q.is_empty
    assert not q.is_full
    kivy_clock.tick()
    assert q.size == 0
    assert q.is_empty
    assert not q.is_full


@p_order
def test_various_statistics_nowait(order):
    from asynckivy_ext.queue import Queue
    q = Queue(capacity=2, order=order)
    assert q.order == order
    assert len(q) == 0
    assert q.capacity == 2
    assert q.size == 0
    assert q.is_empty
    assert not q.is_full
    q.put_nowait(1)
    assert q.size == 1
    assert not q.is_empty
    assert not q.is_full
    q.put_nowait(2)
    assert q.size == 2
    assert not q.is_empty
    assert q.is_full
    q.get_nowait()
    assert q.size == 1
    assert not q.is_empty
    assert not q.is_full
    q.get_nowait()
    assert q.size == 0
    assert q.is_empty
    assert not q.is_full


@p_capacity
def test_get_nowait_while_there_are_no_putters_and_no_items(capacity):
    from asynckivy_ext.queue import Queue, WouldBlock
    q = Queue(capacity=capacity)
    with pytest.raises(WouldBlock):
        q.get_nowait()


@p_capacity
def test_get_nowait_while_there_is_a_putter_but_no_items(capacity):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue, WouldBlock
    q = Queue(capacity=capacity)
    ak.start(q.put('A'))
    with pytest.raises(WouldBlock):
        q.get_nowait()


@p('capacity', [1, 2, ])
def test_put_nowait_while_there_are_no_getters_and_full_of_items(capacity):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue, WouldBlock
    q = Queue(capacity=capacity)
    for i in range(capacity):
        q._c_put(i)
    assert q.is_full
    with pytest.raises(WouldBlock):
        q.put_nowait(99)


@p('capacity', [1, 2, ])
def test_put_nowait_while_there_is_a_getter_and_full_of_items(capacity):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue, WouldBlock
    q = Queue(capacity=capacity)
    for i in range(capacity):
        q._c_put(i)
    assert q.is_full
    ak.start(q.get())
    with pytest.raises(WouldBlock):
        q.put_nowait(99)


def test_put_nowait_to_unbounded_queue_that_has_no_getters():
    from asynckivy_ext.queue import Queue
    q = Queue(capacity=None)
    for i in range(10):
        q._c_put(i)
        assert not q.is_full
    q.put_nowait('A')


def test_put_nowait_to_unbounded_queue_that_has_a_getter():
    import asynckivy as ak
    from asynckivy_ext.queue import Queue
    q = Queue(capacity=None)
    for i in range(10):
        q._c_put(i)
        assert not q.is_full
    ak.start(q.get())
    q.put_nowait('A')


@p('close', [True, False, ])
@p_capacity2
def test_putter_triggers_close(kivy_clock, close, capacity):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue, Closed

    async def producer1(q):
        await q.put('A')
        q.close() if close else q.half_close()
    async def producer2(q):
        with pytest.raises(Closed):
            await q.put('B')
    async def consumer1(q):
        if close:
            with pytest.raises(Closed):
                await q.get()
        else:
            assert await q.get() == 'A'
    async def consumer2(q):
        with pytest.raises(Closed):
            await q.get()

    q = Queue(capacity=capacity)
    p1 = ak.start(producer1(q))
    p2 = ak.start(producer2(q))
    c1 = ak.start(consumer1(q))
    c2 = ak.start(consumer2(q))
    assert not p1.finished
    assert not p2.finished
    assert not c1.finished
    assert not c2.finished
    kivy_clock.tick()
    assert p1.finished
    assert p2.finished
    assert c1.finished
    assert c2.finished


@p('close', [True, False, ])
@p_capacity2
def test_getter_triggers_close(kivy_clock, close, capacity):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue, Closed

    async def producer1(q):
        await q.put('A')
    async def producer2(q):
        if capacity is not None and capacity < 2:
            with pytest.raises(Closed):
                await q.put('B')
        else:
            await q.put('B')
    async def consumer1(q):
        assert await q.get() == 'A'
        q.close() if close else q.half_close()
    async def consumer2(q):
        if close:
            with pytest.raises(Closed):
                await q.get()
        elif capacity is not None and capacity < 2:
            with pytest.raises(Closed):
                await q.get()
        else:
            assert await q.get() == 'B'

    q = Queue(capacity=capacity)
    p1 = ak.start(producer1(q))
    p2 = ak.start(producer2(q))
    c1 = ak.start(consumer1(q))
    c2 = ak.start(consumer2(q))
    assert not p1.finished
    assert not p2.finished
    assert not c1.finished
    assert not c2.finished
    kivy_clock.tick()
    assert p1.finished
    assert p2.finished
    assert c1.finished
    assert c2.finished


@p('capacity', [4, 5, None, ])
@p('order,input,expect', [('fifo', '0123', '0123'), ('lifo', '0123', '3210'), ('small-first', '3102', '0123'), ])
def test_item_order__enough_capacity(kivy_clock, capacity, order, input, expect):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue

    async def producer(q):
        for c in input:
            await q.put(int(c))
        q.half_close()

    async def consumer(q):
        return ''.join([str(i) async for i in q])

    q = Queue(capacity=capacity, order=order)
    p = ak.start(producer(q))
    c = ak.start(consumer(q))
    kivy_clock.tick()
    assert p.finished
    assert c.result == expect


@p('order,input,expect', [('fifo', '0123', '0123'), ('lifo', '0123', '1032'), ('small-first', '3102', '1302'), ])
def test_item_order_2capacity(kivy_clock, order, input, expect):
    '''NOTE: これは仕様というよりは現状の実装に対するtest'''
    import asynckivy as ak
    from asynckivy_ext.queue import Queue

    async def producer(q):
        for c in input:
            await q.put(int(c))
        q.half_close()

    async def consumer(q):
        return ''.join([str(i) async for i in q])

    q = Queue(capacity=2, order=order)
    p = ak.start(producer(q))
    c = ak.start(consumer(q))
    kivy_clock.tick()
    assert p.finished
    assert c.result == expect


@p('order,input,expect', [('fifo', '0123', '0123'), ('lifo', '0123', '2103'), ('small-first', '3102', '0132'), ])
def test_item_3capacity(kivy_clock, order, input, expect):
    '''NOTE: これは仕様というよりは現状の実装に対するtest'''
    import asynckivy as ak
    from asynckivy_ext.queue import Queue

    async def producer(q):
        for c in input:
            await q.put(int(c))
        q.half_close()

    async def consumer(q):
        return ''.join([str(i) async for i in q])

    q = Queue(capacity=3, order=order)
    p = ak.start(producer(q))
    c = ak.start(consumer(q))
    kivy_clock.tick()
    assert p.finished
    assert c.result == expect

@p_order
@p_capacity
def test_scoped_cancel__get(kivy_clock, order, capacity):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue

    async def async_fn(ctx):
        async with ak.open_cancel_scope() as scope:
            ctx['scope'] = scope
            ctx['state'] = 'A'
            await q.get()
            pytest.fail()
        ctx['state'] = 'B'
        await ak.sleep_forever()
        ctx['state'] = 'C'

    q = Queue(capacity=capacity, order=order)
    ctx = {}
    task = ak.start(async_fn(ctx))
    assert ctx['state'] == 'A'
    ctx['scope'].cancel()
    assert ctx['state'] == 'B'
    q.put_nowait('Hello')
    kivy_clock.tick()
    assert ctx['state'] == 'B'
    task._step()
    assert ctx['state'] == 'C'


@p_order
@p_limited_capacity
def test_scoped_cancel__put(kivy_clock, order, capacity):
    import asynckivy as ak
    from asynckivy_ext.queue import Queue

    async def async_fn(ctx):
        async with ak.open_cancel_scope() as scope:
            ctx['scope'] = scope
            ctx['state'] = 'A'
            await q.put('Hello')
            pytest.fail()
        ctx['state'] = 'B'
        await ak.sleep_forever()
        ctx['state'] = 'C'

    q = Queue(capacity=capacity, order=order)
    for __ in range(capacity):
        q.put_nowait('Hello')
    assert q.is_full
    ctx = {}
    task = ak.start(async_fn(ctx))
    assert ctx['state'] == 'A'
    ctx['scope'].cancel()
    assert ctx['state'] == 'B'
    q.get_nowait()
    kivy_clock.tick()
    assert ctx['state'] == 'B'
    task._step()
    assert ctx['state'] == 'C'
