This library has been archived in favor of [asyncgui_ext.queue](https://github.com/asyncgui/asyncgui-ext-queue).
However, it has a quirk caused by a limitation.
If you are using Kivy, you can avoid it as follows:

```python
from asyncqui_ext.queue import Queue
from kivy.clock import Clock

q = Queue(...)
q.transfer_items = Clock.create_trigger(q.transfer_items)
```
