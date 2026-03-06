# Habit Tracker

## Overview
Habit Tracker is a Python CLI application for creating daily or weekly habits, recording completions, and analyzing streaks. It follows a clean architecture with distinct presentation, service, repository, and data layers to keep the codebase testable and maintainable.

## Features
- Create and remove habits with daily or weekly periodicity
- Mark habits as completed with duplicate-prevention logic
- View current habits and streaks
- Analyze longest streaks overall or per habit
- SQLite-backed persistence using SQLAlchemy

## Tech Stack
- Python 3.8+
- SQLAlchemy 1.4 (ORM)
- SQLite (default database)
- pytest (tests)

## Project Structure
```
habitTrackerApp/
├── main.py
├── analytics/
├── database/
├── exceptions/
├── models/
├── repositories/
├── services/
└── tests/
```

## Installation
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
2. Activate it:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the CLI:
```bash
python main.py
```

## Configuration
The application uses SQLite by default. To change the database location or engine, update the database URL in `main.py`:
```python
cli = HabitTrackerCLI(database_url="sqlite:///custom_path/my_habits.db")
```

## Development
Run tests:
```bash
pytest
```

## License
No license file is present in this repository. Add a LICENSE file if you want to specify usage terms.
