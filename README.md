# auto-commit: Your AI-Powered Git Assistant

![CI](https://github.com/Jake-Brewer/auto-commit/actions/workflows/ci.yml/badge.svg)

An autonomous agent that monitors file changes in your projects, generates insightful commit messages using a local LLM, and automates your version control workflow.

## 📖 About The Project

`auto-commit` is designed to be a "set it and forget it" utility for developers who want to maintain a clean and descriptive Git history without the constant interruption of manual commits. It watches your codebase for changes and, when it detects a modification, it uses an AI model to understand the changes and write a commit message that follows best practices.

The key features include:
- **🤖 Automated Commits:** Runs in the background to automatically commit your work.
- **🧠 Intelligent Messaging:** Leverages Large Language Models (LLMs) to generate high-quality, conventional commit messages.
- **✅ User-in-the-Loop:** For files it's unsure about, it queues them up for your review in a simple web UI.
- **⚙️ Customizable:** Uses a hierarchical configuration system (`.gitignore`, `.gitinclude`) to give you fine-grained control over what gets committed.
- **🔒 Privacy-Focused:** Designed to work with a local, containerized LLM, ensuring your code never leaves your machine.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Git
- Docker (for running a local LLM)

### Installation

1. Clone the repo:
   ```sh
   git clone https://github.com/Jake-Brewer/auto-commit.git
   ```
2. Navigate to the project directory:
   ```sh
   cd auto-commit
   ```
3. Install Python dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set up your local LLM (instructions to be added).

## USAGE

To start the agent, run:

```bash
python src/main.py --path /path/to/your/project
```

The agent will then start monitoring the specified directory for changes.

## 🗺️ Roadmap

See the [open issues](https://github.com/Jake-Brewer/auto-commit/issues) for a list of proposed features (and known issues).

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/Jake-Brewer/auto-commit/issues).

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information. 