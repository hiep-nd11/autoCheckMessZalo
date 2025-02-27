# Auto Check Message Zalo Sari

Auto Check Message Zalo Sari

Source uses langchain frameworks and API GPT 4o

## Installation
```bash
$ git clone https://github.com/hiep-nd11/autoCheckMessZalo.git
$ cd autoCheckMessZalo
$ python3 -m venv your_venv_name # create the virtual environment
$ source your_venv_name/bin/activate # activate your venv
$ pip install -r requirements
```

## Test
- Add API Key in src/config.py (OPENAI_API_KEY)

## Rules code
- Code according to PEP8 standard (isort, black formatter extension) or Google style.
- Work with git according to git flow standard (only work on develop branch).
- Use git issue and git project to pull request.
- Pull Request Size: Each pull request (PR) should limit the scope of changes, avoiding too many commits or unrelated changes in a single PR.
- Code Review: Each pull request must be reviewed by at least one other team member. The reviewer should check the code quality, ensure compliance with guidelines, and verify accuracy.
- Commit Message Structure: Commit messages need to be clear, describing the purpose and reason for the commit.
    - Prefix: Use prefixes to categorize the commit, for example:
        + feat: Add a new feature.
        + fix: Fix a bug.
        + refactor: Refactor the code without changing functionality.
        + test: Add or modify tests.
        + docs: Update documentation.
- Docstrings: Each function or class should have a docstring describing its functionality, input parameters, output, and exceptions. Use either the Google style or PEP257 standard.
- Requirements file: library name + current version (Example: numpy==0.0.1).
- Write the function should have (arguments *arg and **kwwarg).

## Weights folder
- You just need to copy the weights folder to the same level as the core folder
