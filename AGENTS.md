# Watch — Repository Guidelines

Watch is a standalone time tracking app for the Tonic ecosystem (Layer 2). It depends on Dock (Layer 1) for ecosystem integration and provides timer APIs that Dock's top-bar widget consumes.

```
Layer 0  Frappe Core
Layer 1  Dock          ← required dependency
Layer 2  Watch         ← this app
```

## Stack

- **Backend:** Frappe v16+, Python 3.14+, MariaDB
- **Frontend:** Vue 3 SPA + TypeScript + Tailwind CSS + FrappeUI

## Dependencies

- `frappe` (framework)
- `dock` (coordination layer — required)

## Build & Development Commands

```bash
# Frontend development (HMR, instant feedback)
cd frontend && npm install && npm run dev

# Production build (only before pushing)
bench build --app watch

# Backend
bench --site <site> migrate
bench run-tests --app watch
bench --site <site> clear-cache
```

**During development, always use `npm run dev`.** Only run `bench build` when preparing to push.

## Coding Style

### TypeScript (mandatory for frontend)

All new code in `frontend/src/` must be TypeScript (`.ts` or `<script lang="ts">`).

### License Headers

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic
```

```typescript
// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic
```

```vue
<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
```

Exceptions: JSON, Markdown, config files, auto-generated files.

### Translation (i18n)

All user-facing strings must be wrapped for translation:

```typescript
import { __ } from '@/composables/useTranslate'
```

```python
from frappe import _
```

After adding strings, update all CSV files in `watch/translations/`.

## Dock Integration

Watch exposes timer APIs that Dock's top-bar widget calls. These are declared in `hooks.py`:

```python
dock_timer_api = {
    "start": "watch.api.timer.start_timer",
    "stop": "watch.api.timer.stop_timer",
    "pause": "watch.api.timer.pause_timer",
    "resume": "watch.api.timer.resume_timer",
    "status": "watch.api.timer.get_timer_state",
}
```

Watch also registers with Dock's app switcher, search, and notifications via hook declarations. No direct import of Dock code.

## Commit Guidelines

```
feat(scope): description
fix(scope): description
docs(scope): description
refactor(scope): description
```

## Git Workflow

- Remote: `upstream` | Default branch: `develop`
- **Always** specify remote and branch: `git push upstream develop`
- **Always** pull before push: `git pull upstream develop --rebase`
- **Never** force push unless explicitly requested

### Preparing a Push

```bash
bench build --app watch                    # 1. Build frontend (if changed)
bench --site <site> clear-cache            # 2. Clear cache
python3 bump_version.py patch              # 3. Bump version
git add -A && git commit -m "feat: ..."    # 4. Commit
git pull upstream develop --rebase         # 5. Pull
git push upstream develop                  # 6. Push
```

### Version Files

`bump_version.py` updates all — never edit just one:

| File | Controls |
|------|----------|
| `VERSION` | Canonical source |
| `watch/__init__.py` | `__version__` |
| `pyproject.toml` | `version` |
| `frontend/package.json` | `"version"` |

## Frappe v16 — Known Issues

- Single DocType `issingle` flag may not sync during migrate — fix via SQL
- Default sort order is `creation` (not `modified`) — always specify sort explicitly
- `has_permission` hooks must return explicit `True`
- State-changing methods require POST (not GET)

## Multi-Agent Safety

- Do **not** create/apply/drop `git stash` entries unless explicitly requested
- Do **not** switch branches unless explicitly requested
- When you see unrecognized files, focus on your changes and leave others untouched

## Dependency Safety

- Exact versions for patched dependencies (no `^` or `~`)
- Patching dependencies requires explicit maintainer approval

## Bug Investigation

- Read source code of relevant dependencies before concluding
- Aim for high-confidence root cause, not surface-level fixes
