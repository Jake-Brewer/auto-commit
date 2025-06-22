import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ChangeHandler(FileSystemEventHandler):
    """Puts all events on a queue."""

    def __init__(self, queue):
        self.queue = queue
        super().__init__()

    def on_any_event(self, event):
        self.queue.put(event)


def start_watching(path, queue):
    """
    Starts the file system watcher on a given path.
    """
    event_handler = ChangeHandler(queue)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"Watcher started on path: {path}")
    return observer

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("Watcher stopped.")
