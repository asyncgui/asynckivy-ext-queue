__all__ = (
    'QueueException', 'WouldBlock', 'Closed',
    'Queue', 'Order', 'QueueState',
    )
import typing as T
import types
import enum
from functools import partial
from collections import deque
from kivy.clock import Clock
from asyncgui import _sleep_forever, Task, _current_task, Cancelled


class QueueState(enum.Enum):
    '''
    Enum class that represents the Queue state.
    '''

    OPENED = enum.auto()
    '''
    All operations are allowed. 

    :meta hide-value:
    '''

    HALF_CLOSED = enum.auto()
    '''
    Putting-operations are not allowed.

    :meta hide-value:
    '''

    CLOSED = enum.auto()
    '''
    Putting/getting-operations are not allowed.

    :meta hide-value:
    '''


class QueueException(Exception):
    '''Base class of all the queue-related exceptions.'''


class WouldBlock(QueueException):
    '''Raised by X_nowait functions if X would block.'''


class Closed(QueueException):
    '''
    Occurs when:

    * one tries to get an item from a queue that is in the ``CLOSED`` state.
    * one tries to get an item from an **empty** queue that is in the ``HALF_CLOSED`` state.
    * one tries to put an item into a queue that is in the ``CLOSED`` or ``HALF_CLOSED`` state.
    '''


Item = T.Any
Order = T.Literal['fifo', 'lifo', 'small-first']


class Queue:
    '''
    :param capacity: Cannot be zero. Unlimited if None.
    '''
    def __init__(self, *, capacity:T.Union[int, None]=None, order:Order='fifo'):
        if capacity is None:
            pass
        elif (not isinstance(capacity, int)) or capacity < 1:
            raise ValueError(f"'capacity' must be either a positive integer or None. (was {capacity!r})")
        self._init_container(capacity, order)
        self._state = QueueState.OPENED
        self._putters = deque[tuple[Task, Item]]()
        self._getters = deque[Task]()
        self._capacity = capacity
        self._order = order
        self._trigger_consume = Clock.create_trigger(self._consume)

    def _init_container(self, capacity, order):
        # If the capacity is 1, there is no point in reordering items.
        # Therefore, for performance reasons, treat the order as 'lifo'.
        if capacity == 1 or order == 'lifo':
            c = []
            c_get = c.pop
            c_put = c.append
        elif order == 'fifo':
            c = deque(maxlen=capacity)
            c_get = c.popleft
            c_put = c.append
        elif order == 'small-first':
            import heapq
            c = []
            c_get = partial(heapq.heappop, c)
            c_put = partial(heapq.heappush, c)
        else:
            raise ValueError(f"'order' must be one of 'lifo', 'fifo' or 'small-first'. (was {order!r})")
        self._c = c
        self._c_get = c_get
        self._c_put = c_put

    def __len__(self) -> int:
        return len(self._c)

    size = property(__len__)
    '''Number of items in the queue. This equals to ``len(queue)``. '''

    @property
    def capacity(self) -> T.Union[int, None]:
        '''Number of items allowed in the queue. None if unbounded.'''
        return self._capacity

    @property
    def is_empty(self) -> bool:
        return not self._c

    @property
    def is_full(self) -> bool:
        return len(self._c) == self._capacity

    @property
    def order(self) -> Order:
        return self._order

    @types.coroutine
    def get(self) -> T.Awaitable[Item]:
        '''
        .. code-block::

            item = await queue.get()
        '''
        if self._state is QueueState.CLOSED:
            raise Closed
        if self._state is QueueState.HALF_CLOSED and self.is_empty:
            raise Closed
        self._trigger_consume()
        task = (yield _current_task)[0][0]  # 本来は except-Cancelled節に置きたい文だが、そこでは yield が使えないので仕方がない
        try:
            return (yield self._getters.append)[0][0]
        except Cancelled:
            self._getters.remove(task)
            raise

    def get_nowait(self) -> Item:
        '''
        .. code-block::

            item = queue.get_nowait()
        '''
        if self._state is QueueState.CLOSED:
            raise Closed
        if self.is_empty:
            if self._state is QueueState.HALF_CLOSED:
                raise Closed
            raise WouldBlock
        self._trigger_consume()
        return self._c_get()

    @types.coroutine
    def put(self, item) -> T.Awaitable:
        '''
        .. code-block::

            await queue.put(item)
        '''
        if self._state is not QueueState.OPENED:
            raise Closed
        self._trigger_consume()
        row = ((yield _current_task)[0][0], item, )
        self._putters.append(row)
        try:
            yield _sleep_forever
        except Cancelled:
            self._putters.remove(row)
            raise

    def put_nowait(self, item):
        '''
        .. code-block::

            queue.put_nowait(item)
        '''
        if self._state is not QueueState.OPENED:
            raise Closed
        if self.is_full:
            raise WouldBlock
        self._trigger_consume()
        self._c_put(item)

    def half_close(self):
        '''Partially closes the queue. No further putting-opeations are allowed. '''
        if self._state is not QueueState.OPENED:
            return
        self._state = QueueState.HALF_CLOSED

        # LOAD_FAST
        pop_putter = self._pop_putter
        pop_getter = self._pop_getter
        C = Closed
    
        while (putter := pop_putter()[0]) is not None:
            putter._throw_exc(C)
        if not self.is_empty:
            return
        while (getter := pop_getter()) is not None:
            getter._throw_exc(C)

    def close(self):
        '''
        Fully closes the queue. No further putting/getting-operations are allowed.
        All items in the queue are discarded.
        '''
        if self._state is QueueState.CLOSED:
            return
        self._state = QueueState.CLOSED
        self._c.clear()

        # LOAD_FAST
        C = Closed
        pop_putter = self._pop_putter
        pop_getter = self._pop_getter

        while (task := pop_putter()[0]) is not None:
            task._throw_exc(C)
        while (task := pop_getter()) is not None:
            task._throw_exc(C)

    async def __aiter__(self):
        '''
        Keeps retrieving items from the queue until it is closed.

        .. code-block::

            async for item in queue:
                ...

        which is equivalent to:

        .. code-block::

            try:
                while True:
                    item = await queue.get()
                    ...
            except Closed:
                pass
        '''
        try:
            while True:
                yield await self.get()
        except Closed:
            pass

    def _consume(self, dt):
        # LOAD_FAST
        getters = self._getters
        putters = self._putters
        pop_putter = self._pop_putter
        pop_getter = self._pop_getter
        c_put = self._c_put
        c_get = self._c_get
        Closed_ = Closed
        HALF_CLOSED = QueueState.HALF_CLOSED

        while True:
            while not self.is_full:
                putter, item = pop_putter()
                if putter is None:
                    break
                c_put(item)
                putter._step()
            if (not getters) or self.is_empty:
                break
            while not self.is_empty:
                getter = pop_getter()
                if getter is None:
                    break
                getter._step(c_get())
            else:
                if self._state is HALF_CLOSED:
                    while (getter := pop_getter()) is not None:
                        getter._throw_exc(Closed_)
            if (not putters) or self.is_full:
                break
        self._trigger_consume.cancel()


    def _pop_getter(self) -> T.Union[Task, None]:
        '''Take out a next getter. Return None if no one is available.'''
        getters = self._getters
        return getters.popleft() if getters else None

    def _pop_putter(self, _none_none=(None, None, )) -> tuple[Task, Item]:
        '''Take out a next putter and its item. Return (None, None) if no one is available.'''
        putters = self._putters
        return putters.popleft() if putters else _none_none
