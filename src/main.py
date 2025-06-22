import logging
import threading
import time
from queue import Queue

from commit_worker import CommitWorkerPool
from config import load_config
from config_manager import ConfigurationManager
from git_ops import GitRepo
from llm_comm import LLMCommitGenerator
from review_queue import ReviewQueue
from ui_backend import create_ui_backend
from watcher import start_watching


def main():
    """
    Main entry point for the auto-commit agent.
    """
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading configuration: {e}")
        return

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("AutoCommit")

    logger.info(f"Auto-commit agent started. Watching '{config.watch_directory}'")

    repo = GitRepo(config.watch_directory)
    if not repo.repo:
        logger.error("Could not initialize Git repository. Exiting.")
        return

    event_queue = Queue()

    path_to_watch = config.watch_directory
    observer = start_watching(path_to_watch, event_queue)

    # Initialize configuration manager
    config_manager = ConfigurationManager(config.watch_directory)

    # Add default ignore patterns safely
    config_manager.safe_add_default_ignores()

    # Initialize review queue
    review_queue = ReviewQueue("review_queue.db")

    # Initialize LLM generator with config
    llm_generator = LLMCommitGenerator(
        base_url=config.llm.base_url,
        model_name=config.llm.model_name,
        enable_linear_fallback=config.llm.enable_linear_fallback,
        fallback_team_id=config.llm.fallback_team_id,
    )

    # Start the commit worker pool
    worker_pool = CommitWorkerPool(
        event_queue, config_manager, review_queue, num_workers=2
    )
    worker_pool.start()

    # Start UI backend in a separate thread
    ui_backend = create_ui_backend(review_queue, config_manager)
    ui_thread = threading.Thread(
        target=ui_backend.run,
        kwargs={"host": "127.0.0.1", "port": 8000, "debug": False},
        daemon=True,
    )
    ui_thread.start()
    logger.info("UI backend started on http://127.0.0.1:8000")

    last_commit_time = time.time()
    commit_interval = 10  # seconds

    try:
        while True:
            # Commit changes on a timer if the repo is dirty
            if time.time() - last_commit_time > commit_interval:
                staged_diff = repo.get_diff("STAGED")
                if repo.get_status() or staged_diff:
                    logger.info("Changes detected, generating commit message...")
                    repo.add_all()

                    # Use staged diff for commit message generation
                    diff_for_llm = repo.get_diff("STAGED")

                    # Get changed file paths for LLM context
                    status_output = repo.get_status()
                    changed_files = []
                    if status_output:
                        for line in status_output.split("\n"):
                            if line.strip():
                                # Parse git status porcelain format
                                file_path = line[3:].strip()
                                changed_files.append(file_path)

                    message = llm_generator.generate_commit_message(
                        diff_for_llm, changed_files
                    )
                    if message:
                        logger.info(f"Committing with message: {message}")
                        repo.commit(message)
                        last_commit_time = time.time()
                    else:
                        logger.warning(
                            "Commit message generation failed. " "No changes committed."
                        )
                else:
                    logger.debug("No changes to commit.")

                last_commit_time = time.time()

            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        worker_pool.stop()
        observer.stop()
    observer.join()
    logger.info("Auto-commit agent stopped.")


if __name__ == "__main__":
    main()
