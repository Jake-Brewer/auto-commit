import time
from queue import Queue
from watcher import start_watching
from config import load_config
from file_filter import should_process_path
from git_ops import GitRepo
from llm_comm import generate_commit_message


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
    
    repo = GitRepo(config.watch_directory)
    if not repo.repo:
        print("Could not initialize Git repository. Exiting.")
        return

    event_queue = Queue()

    path_to_watch = config.watch_directory
    observer = start_watching(path_to_watch, event_queue)

    last_commit_time = time.time()
    commit_interval = 10  # seconds

    try:
        while True:
            # Non-blocking check of the queue
            while not event_queue.empty():
                event = event_queue.get_nowait()
                if should_process_path(
                    event.src_path,
                    config.include_patterns,
                    config.exclude_patterns
                ):
                    print(f"Queued change in: {event.src_path}")

            # Commit changes on a timer if the repo is dirty
            if time.time() - last_commit_time > commit_interval:
                staged_diff = repo.get_diff("STAGED")
                if repo.get_status() or staged_diff:
                    print("Changes detected, generating commit message...")
                    repo.add_all()
                    
                    # Use staged diff for commit message generation
                    diff_for_llm = repo.get_diff("STAGED")
                    
                    message = generate_commit_message(diff_for_llm)
                    if message:
                        print(f"Committing with message:\n---\n{message}\n---")
                        repo.commit(message)
                        last_commit_time = time.time()
                    else:
                        print("Commit message generation failed. No changes committed.")
                else:
                    print("No changes to commit.")
                
                last_commit_time = time.time()

            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("Auto-commit agent stopped.")


if __name__ == "__main__":
    main() 