# Changelog

## 0.1.3

- Fix timer auto-stop scheduled task not respecting per-user timezone
- Fix locked entry check using UTC instead of site timezone
- Add `bulk_delete` endpoint for time entries
- Add `get_all_budgets` endpoint for budget overview
- Improve CSV export to include tag columns

## 0.1.2

- Add Pomodoro / focus mode (`start_focus`, `end_focus_session`, `skip_break`, `end_focus`)
- Add day templates (`save_day_template`, `apply_day_template`)
- Add billing module with summary, CSV export, and extensible billing actions
- Add `dock_bridges` hook for ERPNext Timesheet sync visibility in Dock
- Fix weekly summary not respecting configured work days
- Fix budget notifications publishing to wrong user

## 0.1.1

- Add ERPNext bridge (`sync_day`, `sync_entry`, `bulk_sync`, `get_sync_status`, `test_connection`)
- Add integration settings for Slack, Linear, and GitHub
- Add `dock_activity_sources` hook for Dock activity feed
- Add `dock_notification_types` for budget warnings
- Add browser extension token generation and revocation
- Fix timer state not clearing after auto-stop
- Fix tag merge not updating budget associations

## 0.1.0

- Initial release
- Watch Entry, Watch Timer, Watch Tag, Watch Settings, Watch User Settings DocTypes
- Timer with start, stop, pause, resume state machine
- Time entry CRUD with daily and weekly summaries
- Tag management with budgets
- Dock integration: app registry, timer widget, global search, settings panel
- Entry templates and favorites
- CSV export for time entries
- Keyboard shortcuts
- `if_owner` row-level permissions with Time Tracker role
