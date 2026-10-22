# Submission Verification Checklist

- [x] All required files listed in `required_files.participant.md` are present.
- [x] Streamlit UI can create, open, and continue multi-turn conversations.
- [x] All numerical answers are grounded in Gold data, explicitly stating filters, periods, and units.
- [x] Gold credentials are read-only and queries are protected by AST SQLGlot guard and 5-second statement timeout.
- [x] Out-of-scope requests and indirect prompt injection attempts via `exception_note` are safely handled.
- [x] Token B cannot list, read, or send messages to Token A's conversations; test evidence included (`HTTP 404`).
- [x] At least 12 evaluation test cases with expected, actual, and status documented (14 cases in `docs/evaluation.md`).
- [x] `README.md` includes setup for Windows PowerShell and macOS/Linux, automated test instructions, and production limitations.
- [x] Participant Dockerfile builds cleanly with `docker compose build`.
- [x] `docker compose up --build` runs API and UI on container ports 8000 and 8501; UI connects to `http://api:8000`.
- [x] `.dockerignore` excludes `.env`, virtual environments, cache, and SQLite files; credentials are provided at runtime only.
- [x] Conversations persist after API service restart because SQLite utilizes a persistent Docker named volume.
- [x] 5–7 minute demo covers happy path, contextual follow-up, refusal/no data, prompt injection, and IDOR defense.
- [x] No secrets, SQLite database binaries, or real personal data included in the submission repository.
