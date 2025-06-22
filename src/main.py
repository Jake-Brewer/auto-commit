import time
from queue import Queue
from watcher import start_watching
from config import load_config


def main():
    """
    Main entry point for the auto-commit agent.
    """
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading configuration: {e}")
        return

    print(f"Auto-commit agent started. Watching '{config.watch_directory}'")
    event_queue = Queue()

    path_to_watch = config.watch_directory
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