import time
from queue import Queue
from watcher import start_watching


def main():
    """
    Main entry point for the auto-commit agent.
    """
    print("Auto-commit agent started.")
    event_queue = Queue()

    # For now, we will just watch the current directory.
    # This will be made configurable later.
    path_to_watch = '.'
    observer = start_watching(path_to_watch, event_queue)

    try:
        while True:
            if not event_queue.empty():
                event = event_queue.get()
                print(
                    f"Main loop consumed event: {event.src_path} - "
                    f"{event.event_type}"
                )
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("Auto-commit agent stopped.")


if __name__ == "__main__":
    main() 