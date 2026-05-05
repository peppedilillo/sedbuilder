### Setup

Clone the repository and install with development dependencies:

```bash
git clone https://github.com/peppedilillo/sedbuilder.git
cd sedbuilder
pip install -e ".[dev, docs]"
# or with uv
uv sync --extra dev --extra docs
# next line will route queries to test server. 
# use only on SSDC internal network 
source dev.env 
```

### Pre-commit Hooks

Install pre-commit hooks to automatically format code before commits:

```bash
pre-commit install
```

This runs `black` (line length 120) and `isort` (Google profile) automatically.

### Running Tests

```bash
pytest
```

You must first `cd` into the project directory.

To run smoke tests against the live server:

```bash
pytest --smoke
```

### Pushing to gitlab

Setup the GitLab remote repository:

```shell
git remote add gitlab git@gitrepo.ssdc.asi.it:sedbuilder/sedbuilder.git
git push -u gitlab
```

Push to GitHub and GitLab:

```python
# pushes to github
git push origin
# pushes to gitlab
git push gitlab
```

### Building and shipping Documentation

```bash
pip install -e ".[docs]"
mkdocs serve
mkdocs gh-deploy
```