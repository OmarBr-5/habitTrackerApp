# Habit Tracker

Simple habit tracking application with analytics.

## Quick Start

1. **Create virtual environment:**

   ```bash
   python -m venv .venv
   ```

2. **Activate virtual environment:**
   - Windows: `.venv\Scripts\activate`
   - Mac/Linux: `source .venv/bin/activate`

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Features

- Add daily or weekly habits
- Track completions
- View analytics and streaks

## Data Storage

- Uses SQLite database (`habit_tracker.db`)

## Tests

Run all tests with:

```bash
pytest
```
