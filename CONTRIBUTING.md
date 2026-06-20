# Contributing to Study Assistant AI

Thanks for your interest in contributing! 🎉 Contributions of all kinds are
welcome — bug reports, feature ideas, docs, and code.

## Getting set up

```bash
git clone https://github.com/swaroopramv/study-assistant-ai.git
cd study-assistant-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install ruff pytest          # dev tools
```

Make sure [Ollama](https://ollama.com) is installed and the models are pulled:

```bash
ollama pull ministral-3:8b
ollama pull nomic-embed-text
```

## Development workflow

1. Create a branch: `git checkout -b feature/my-change`
2. Make your changes (keep them focused).
3. Format and lint:
   ```bash
   ruff format .
   ruff check .
   ```
4. Run the tests:
   ```bash
   pytest
   ```
5. Commit with a clear message and open a Pull Request.

## Guidelines

- Keep functions small and add type hints where practical.
- Add or update tests for any behaviour you change.
- Tests must run **offline** (no live Ollama server) so CI stays reliable —
  mock external calls where needed.
- The CI workflow (`.github/workflows/ci.yml`) runs ruff and pytest on every
  push and pull request; please ensure it passes.

## Reporting bugs

Open an issue with:
- What you expected vs. what happened
- Steps to reproduce
- Your OS, Python version, and Ollama model

Happy hacking! 🚀
