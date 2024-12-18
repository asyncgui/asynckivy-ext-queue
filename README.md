# Warning

This library has been archived in favor of [asyncgui_ext.synctools](https://github.com/asyncgui/asyncgui-ext-synctools).

# Queue

Extension for `asynckivy` programs.

```python
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
```

```text
produced A
consumed A
produced B
consumed B
produced C
consumed C
```

## Installation

It's recommended to pin the minor version, because if it changed, it means some *important* breaking changes occurred.

```text
poetry add asynckivy-ext-queue@~0.2
pip install "asynckivy-ext-queue>=0.2,<0.3"
```

## Tested on

- CPython 3.9 + Kivy 2.2.1
- CPython 3.10 + Kivy 2.2.1
- CPython 3.11 + Kivy 2.2.1
