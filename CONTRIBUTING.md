Thanks for your interest in contributing!

Quick checklist:
- Use a virtualenv and Python 3.10 (recommended).
- Copy `.env.example` → `.env` and fill `OPENAI_API_KEY` (do NOT commit real keys).
- Run tests locally: `pytest -q`.
- Run linting on focused modules: `flake8 reverie/backend_server/persona reverie/backend_server/persona/prompt_template`.
- Consider using `pre-commit` for automatic formatting: `pip install pre-commit && pre-commit install`.

If you plan to do larger refactors, open an issue describing the scope first so we can coordinate and add tests around behavior.
