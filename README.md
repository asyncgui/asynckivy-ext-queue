This repository no longer provides source code and has been replaced by [asyncgui_ext.queue](https://github.com/asyncgui/asyncgui-ext-queue).
However, that library has a quirk due to a limitation.
If you are using Kivy, you can avoid it as follows:

```python
from asyncqui_ext.queue import Queue
from kivy.clock import Clock

q = Queue(...)
q.transfer_items = Clock.create_trigger(q.transfer_items)
```
