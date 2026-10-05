# KindlePro

Kindle-friendly browser hub with chat, user topics, a board, games, and tools. Basic HTML + almost no JS.

## Layout

- `frontend/` — static site (deploy to GitHub Pages). Set your Render URL in `frontend/config.js`.
- `backend/` — Node.js + Express API (deploy to Render). Neon Postgres for storage.

## Backend (Render)

1. `cd backend && npm install`
2. Create a Neon project and get the connection string.
3. Run `schema.sql` against your Neon database (SQL editor in Neon console).
4. Render: new Web Service, root dir `backend`, build `npm install`, start `node server.js`.
   Env vars: `DATABASE_URL` (Neon string), `PORT` (Render sets it).
5. `curl https://your-app.onrender.com/api/chat` to test.

## Frontend (GitHub Pages)

1. Edit `frontend/config.js` → set `API` to your Render URL.
2. Push `frontend/` to a GitHub Pages repo (or use the `docs/` trick / `gh-pages` branch).
3. Browse to the Pages URL from your Kindle.

## Notes

- Old Kindle browsers don't support `fetch`, so the frontend uses XMLHttpRequest and simple `onclick` handlers.
- Chat pages auto-refresh via `<meta refresh>`; games run fully client-side (Hangman, Guess, TicTacToe, RPS).

## Features

- Login required for chat, topics, and board (`/api/chat`, `/api/topics`, `/api/threads` all need a token)
- First registered user becomes **admin**; rest are normal users
- Admin panel (`admin.html`): user list with last IP, ban/unban, per-user IP history
- Honeypot-free moderation: banned users get `403` on all posting endpoints
- Sidebar layout, larger text for readability

## Old Python version

`server.py` is the original all-in-one Python version; kept for local use only (`python3 server.py`). It is not used on GitHub Pages/Render.
