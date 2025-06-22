import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ChangeHandler(FileSystemEventHandler):
    """Logs all events captured."""

    def on_moved(self, event):
        what = 'directory' if event.is_directory else 'file'
        print(f"Moved {what}: from {event.src_path} to {event.dest_path}")

    def on_created(self, event):
        what = 'directory' if event.is_directory else 'file'
        print(f"Created {what}: {event.src_path}")

    def on_deleted(self, event):
        what = 'directory' if event.is_directory else 'file'
        print(f"Deleted {what}: {event.src_path}")

    def on_modified(self, event):
        what = 'directory' if event.is_directory else 'file'
        print(f"Modified {what}: {event.src_path}")


def start_watching(path='.'):
    """
    Starts the file system watcher on a given path.
    """
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"Watcher started on path: {path}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("Watcher stopped.") 