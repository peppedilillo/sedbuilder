# Test Data

This directory contains JSON fixtures from the SED Builder API used for testing.

## Updating Test Data

When the upstream API changes, regenerate these fixtures:

```bash
cd tests
python fetch_test_data.py
```

This will query the API for predefined test sources and save responses as JSON files.

## Filename Format

Files are named as `{ra}_{dec}.json` where dots are replaced with 'd':
- Example: RA=194.04625, Dec=-5.789167 → `194d04625_-5d789167.json`
