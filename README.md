<p align="center">
  <h1 align="center">Watch</h1>
  <p align="center">Standalone time tracking for the Frappe ecosystem</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.1-blue.svg>
  <a href="https://www.gnu.org/licenses/agpl-3.0">
    <img src="https://img.shields.io/badge/License-AGPL_v3-blue.svg" alt="License: AGPL v3">
  </a>
</p>

---

**Watch** is a modern, standalone time tracking app built on the [Frappe Framework](https://frappeframework.com). It gives you a one-click timer, clean daily and weekly views, a flexible tag system, and optional ERPNext integration — all in a single, free app.

## Features

- **One-click timer** — Start, pause, and stop with a single click or keyboard shortcut
- **Time entries** — Date, start/end time, duration, description, billable flag
- **Tags** — Organize entries with reusable labels (clients, categories, etc.)
- **Daily & weekly views** — See where your time goes at a glance
- **ERPNext bridge** — Optionally sync time entries to ERPNext Timesheets
- **Export** — Download entries as CSV or Excel

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Frappe v15+, Python 3.10+, MariaDB |
| Frontend | Vue 3, TypeScript, Tailwind CSS, Frappe UI |
| Build | Vite |

## Installation

Install using the [Frappe Bench](https://frappeframework.com/docs/user/en/bench) CLI:

```bash
bench get-app https://github.com/tonic-6101/watch.git
bench --site your-site.localhost install-app watch
```

## Development Setup

```bash
# Install the app in development mode
bench get-app https://github.com/tonic-6101/watch.git
bench --site your-site.localhost install-app watch

# Start the frontend dev server
cd apps/watch/frontend
yarn install
yarn dev
```

## Contributing

Contributions are welcome! This project uses `pre-commit` for code formatting and linting:

```bash
cd apps/watch
pre-commit install
```

Pre-commit runs the following tools automatically:

- **ruff** — Python linting and formatting
- **eslint** — TypeScript/JavaScript linting
- **prettier** — Code formatting
- **pyupgrade** — Python syntax modernization

## License

This project is licensed under the [GNU Affero General Public License v3.0](license.txt).

```
SPDX-License-Identifier: AGPL-3.0-or-later
Copyright (C) 2024-2026 Tonic
```
