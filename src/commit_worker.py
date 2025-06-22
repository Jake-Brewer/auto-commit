"""
Commit Worker module for processing file change events.

This module implements the CommitWorker class that runs in a thread pool
to process file change events from the queue and orchestrate the analysis
and commit process.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue
from typing import Optional

from watchdog.events import FileSystemEvent

from config_manager import ConfigurationManager, FileAction
from review_queue import ReviewQueue


class CommitWorker:
    """
    Worker class that processes file change events from a thread-safe queue.

    This worker runs in a thread pool and is responsible for dequeuing events
    and orchestrating the analysis and commit process.
    """

    def __init__(
        self,
        event_queue: Queue,
        config_manager: ConfigurationManager,
        review_queue: ReviewQueue,
        worker_id: int = 0,
    ):
        """
        Initialize the CommitWorker.

        Args:
            event_queue: Thread-safe queue containing file system events
            config_manager: Configuration manager for file filtering
            review_queue: Queue for files needing human review
            worker_id: Unique identifier for this worker instance
        """
        self.event_queue = event_queue
        self.config_manager = config_manager
        self.review_queue = review_queue
        self.worker_id = worker_id
        self.logger = logging.getLogger(f"CommitWorker-{worker_id}")
        self.running = False

    def start(self):
        """Start the worker thread."""
        self.running = True
        self.logger.info(f"CommitWorker {self.worker_id} starting...")

    def stop(self):
        """Stop the worker thread."""
        self.running = False
        self.logger.info(f"CommitWorker {self.worker_id} stopping...")

    def process_event(self, event: FileSystemEvent) -> bool:
        """
        Process a single file system event.

        Args:
            event: The file system event to process

        Returns:
            True if event was processed successfully, False otherwise
        """
        try:
            self.logger.debug(
                f"Processing event: {event.src_path} - {event.event_type}"
            )

            # Check file action based on configuration
            action = self.config_manager.get_file_action(event.src_path)

            if action == FileAction.IGNORE:
                self.logger.debug(f"Ignoring file: {event.src_path}")
                return True
            elif action == FileAction.REVIEW:
                self.logger.info(f"File needs review: {event.src_path}")
                # Add to review queue
                self.review_queue.add_item(
                    file_path=event.src_path,
                    event_type=event.event_type,
                    reason="Ambiguous include/ignore rules",
                )
                return True
            elif action == FileAction.INCLUDE:
                self.logger.info(f"Processing file: {event.src_path}")
                # TODO: Integrate with git operations
                # TODO: Integrate with LLM commit message generation

            self.logger.info(f"Worker {self.worker_id} processed: {event.src_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing event {event.src_path}: {e}")
            return False

    def run(self):
        """
        Main worker loop that processes events from the queue.

        This method runs continuously until stopped, pulling events
        from the queue and processing them.
        """
        self.start()

        while self.running:
            try:
                # Try to get an event from the queue with a timeout
                event = self.event_queue.get(timeout=1.0)

                # Process the event
                success = self.process_event(event)

                # Mark the task as done
                self.event_queue.task_done()

                if not success:
                    self.logger.warning(f"Failed to process event: {event.src_path}")

            except Empty:
                # No events in queue, continue
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error in worker loop: {e}")
                time.sleep(0.1)  # Brief pause to prevent tight error loops


class CommitWorkerPool:
    """
    Manages a pool of CommitWorker threads for processing file change events.
    """

    def __init__(
        self,
        event_queue: Queue,
        config_manager: ConfigurationManager,
        review_queue: ReviewQueue,
        num_workers: int = 2,
    ):
        """
        Initialize the CommitWorkerPool.

        Args:
            event_queue: Thread-safe queue containing file system events
            config_manager: Configuration manager for file filtering
            review_queue: Queue for files needing human review
            num_workers: Number of worker threads to create
        """
        self.event_queue = event_queue
        self.config_manager = config_manager
        self.review_queue = review_queue
        self.num_workers = num_workers
        self.workers: list[CommitWorker] = []
        self.executor: Optional[ThreadPoolExecutor] = None
        self.logger = logging.getLogger("CommitWorkerPool")

    def start(self):
        """Start the worker pool."""
        self.logger.info(f"Starting CommitWorkerPool with {self.num_workers} workers")

        # Create the thread pool executor
        self.executor = ThreadPoolExecutor(
            max_workers=self.num_workers, thread_name_prefix="CommitWorker"
        )

        # Create and start workers
        for i in range(self.num_workers):
            worker = CommitWorker(
                self.event_queue, self.config_manager, self.review_queue, worker_id=i
            )
            self.workers.append(worker)

            # Submit worker to thread pool
            self.executor.submit(worker.run)

        self.logger.info("CommitWorkerPool started successfully")

    def stop(self):
        """Stop the worker pool and all workers."""
        self.logger.info("Stopping CommitWorkerPool...")

        # Stop all workers
        for worker in self.workers:
            worker.stop()

        # Shutdown the executor
        if self.executor:
            self.executor.shutdown(wait=True)

        self.logger.info("CommitWorkerPool stopped")

    def wait_for_completion(self):
        """Wait for all queued events to be processed."""
        self.event_queue.join()
