# Agent Commands for COPY Project

## Linting
To lint the code and fix issues automatically:
```
. .venv/bin/activate && ruff check app.py --fix
```

## Testing
To run the automated tests:
```
. .venv/bin/activate && python test_app.py
```

## Notes
- Ensure virtual environment is set up with `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt ruff`
- Tests clean up transfer/ and slugs.json before running for isolation