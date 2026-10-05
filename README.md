# KindlePro

Kindle-friendly browser hub with chat, user topics, a board, games, and tools. Basic HTML + minimal JS.

This repo contains the **static frontend only** (deploy to GitHub Pages). The Node/Express + Neon backend lives in a separate folder/repo (the API).

## Setup

1. Edit `config.js` → set `API` to your backend URL (e.g. `https://your-app.onrender.com`).
2. Push to GitHub and enable GitHub Pages on the `main` branch.
3. Open the Pages URL from your Kindle.

## Features

- Login required for chat, topics, and board
- First registered user becomes admin; admin can ban users and view IP history (`admin.html`)
- Sidebar layout, clean professional styling
- Games (Hangman, Guess, TicTacToe, RPS) run fully client-side
- Tools: calculator, reading time, unit converter
