from watcher import start_watching


def main():
    """
    Main entry point for the auto-commit agent.
    """
    print("Auto-commit agent started.")
    # For now, we will just watch the current directory.
    # This will be made configurable later.
    start_watching('.')


if __name__ == "__main__":
    main() 