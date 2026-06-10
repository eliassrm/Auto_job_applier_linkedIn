# Auto Job Applier LinkedIn - Project Structure

This document is for developers and maintainers working on this repository. It maps the current source tree, runtime flow, ownership boundaries, generated files, and the safest places to make changes.

## Project Role

This is a Python/Selenium automation project for LinkedIn job applications. It can:

- open a Chrome/Selenium session;
- wait for LinkedIn login;
- search jobs using configured terms and filters;
- skip jobs based on company, description, experience, and application state;
- answer LinkedIn Easy Apply questions from configured answers and optional AI providers;
- upload a configured resume when available;
- record applied, external, failed, and skipped jobs to CSV/log files;
- expose a small Flask UI for viewing applied job history.

## Source Tree

Generated/runtime folders are shown separately so they do not get confused with maintainable source.

```text
Auto_job_applier_linkedIn/
├── README.md
├── STRUCTURE.md
├── LICENSE
├── .gitignore
├── .github/
│   └── FUNDING.yml
├── app.py
├── runAiBot.py
├── config/
│   ├── personals.py
│   ├── questions.py
│   ├── resume.py
│   ├── search.py
│   ├── secrets.py
│   └── settings.py
├── modules/
│   ├── clickers_and_finders.py
│   ├── helpers.py
│   ├── open_chrome.py
│   ├── validator.py
│   ├── ai/
│   │   ├── deepseekConnections.py
│   │   ├── geminiConnections.py
│   │   ├── openaiConnections.py
│   │   └── prompts.py
│   ├── images/
│   │   ├── EasyApplyButton/
│   │   └── LinkedIn/
│   ├── javascript/
│   │   └── unfollow_companies.js
│   ├── resumes/
│   │   ├── extractor.py
│   │   └── generator.py
│   └── __deprecated__/
├── setup/
│   ├── setup.sh
│   ├── windows-setup.bat
│   └── windows-setup.ps1
└── templates/
    └── index.html
```

## Runtime And Generated Files

These files/folders are produced locally while running the bot and should be treated as operational state, not source design:

- `.venv/`: local Python virtual environment.
- `__pycache__/` and `*.pyc`: Python bytecode cache.
- `all excels/`: CSV output history.
- `all resumes/`: resume input/output location used by config.
- `logs/`: `log.txt` and screenshots from failures/manual intervention.
- `.git/`: local Git metadata.

The current `.gitignore` excludes several of these, plus `config/personals.py` and `secrets.py`. Be careful: this repository currently has `config/personals.py` and `config/secrets.py` tracked, so do not commit private values.

## Entry Points

### `runAiBot.py`

Primary automation entry point.

Responsibilities:

- imports all active config modules;
- validates configuration through `modules.validator.validate_config`;
- creates/uses the Chrome session from `modules.open_chrome`;
- waits for manual LinkedIn login confirmation;
- applies search filters;
- loops through search terms and result pages;
- skips duplicate, blacklisted, over-experience, and irrelevant jobs;
- performs Easy Apply flows or collects external application links;
- writes applied and failed job records to CSV files;
- writes logs and screenshots.

Important functions:

- `main()`: top-level orchestration.
- `run(total_runs)`: one search/apply cycle.
- `apply_to_jobs(search_terms)`: main search result loop.
- `apply_filters()`: LinkedIn filter UI automation.
- `get_job_main_details(...)`: reads card-level job metadata.
- `get_job_description()`: reads job description and skip signals.
- `answer_questions(...)`: handles Easy Apply form fields.
- `external_apply(...)`: handles non-Easy Apply links.
- `submitted_jobs(...)`: writes successful applications/external links.
- `failed_job(...)`: writes failure history.
- `screenshot(...)`: stores failure screenshots.

### `app.py`

Flask history UI entry point.

Routes:

- `GET /`: renders `templates/index.html`.
- `GET /applied-jobs`: returns applied jobs from `all excels/all_applied_applications_history.csv`.
- `PUT /applied-jobs/<job_id>`: marks an external job as applied by updating `Date Applied`.

Run it with:

```bash
python app.py
```

Then open:

```text
http://localhost:5000
```

## Runtime Flow

```text
python runAiBot.py
  -> import config values
  -> modules.open_chrome creates Chrome driver, wait, actions
  -> validate_config()
  -> alert user and wait for LinkedIn login confirmation
  -> optionally create AI client
  -> run()
      -> apply_to_jobs(search_terms)
          -> apply filters
          -> paginate LinkedIn results
          -> skip already applied or rejected jobs
          -> read description, HR info, posted date, skills
          -> Easy Apply:
              -> answer questions
              -> upload resume when available
              -> optionally pause before submit
              -> submit and write success CSV
          -> External Apply:
              -> collect external URL
              -> write success CSV with pending date
          -> on error:
              -> screenshot
              -> write failed CSV
  -> print run summary
  -> close browser and AI client
```

## Configuration Files

All config files are Python modules. Most values are imported with `from config.<file> import *`, so variable names are part of the runtime contract.

### `config/personals.py`

Stores personal identity and equal-employment style answers.

Use for:

- legal name parts;
- phone number;
- city/address fields;
- ethnicity/gender/disability/veteran answers.

Maintenance note: keep private data out of commits. Prefer a local-only file or template workflow if this repo is shared.

### `config/questions.py`

Stores application answer defaults.

Use for:

- `default_resume_path`;
- years of experience;
- visa sponsorship answer;
- portfolio and LinkedIn profile links;
- citizenship answer;
- desired/current compensation;
- notice period;
- headline, summary, cover letter, AI user information;
- manual pause behavior.

### `config/search.py`

Stores LinkedIn search and skip logic.

Use for:

- `search_terms`;
- `search_location`;
- result switching/randomization;
- LinkedIn filter values;
- Easy Apply-only mode;
- company/job-description blacklist and exception lists;
- security clearance and experience thresholds.

### `config/secrets.py`

Stores LinkedIn and AI connection credentials.

Use for:

- LinkedIn username/password fallback;
- `use_AI`;
- `ai_provider`;
- `llm_api_url`;
- `llm_api_key`;
- `llm_model`;
- `llm_spec`;
- streaming behavior.

Maintenance note: this file must not expose real credentials in source control.

### `config/settings.py`

Stores bot behavior and output paths.

Use for:

- tab handling and follow-company behavior;
- continuous run behavior;
- generated resume path;
- applied/failed CSV paths;
- logs path;
- click delay;
- headless/background behavior;
- Chrome safe mode, extension handling, smooth scroll, screen awake, stealth mode;
- AI error alert behavior.

### `config/resume.py`

Currently appears separate from the main active import path. `runAiBot.py` imports `config.questions.default_resume_path`, not `config.resume`. Treat `config/resume.py` as experimental or legacy unless you wire it into the active flow deliberately.

## Core Modules

### `modules/open_chrome.py`

Creates the Selenium Chrome session.

Responsibilities:

- create output directories before running;
- select normal Selenium or `undetected_chromedriver` based on `stealth_mode`;
- optionally run headless;
- reuse the default Chrome profile when possible;
- fall back to a temporary/guest profile when needed;
- expose global `options`, `driver`, `actions`, and `wait`.

Developer note: importing this module has side effects because it creates the browser session at import time.

### `modules/helpers.py`

Shared operational helpers.

Responsibilities:

- create directories;
- locate Chrome profile folders;
- print and append logs;
- random timing buffer;
- manual login retry dialog;
- parse LinkedIn posted-date text;
- convert salary-like values;
- parse JSON responses;
- truncate large values before writing CSV.

### `modules/clickers_and_finders.py`

Selenium UI utility layer.

Responsibilities:

- click buttons/spans;
- select LinkedIn filters;
- click boolean switches;
- find elements by class/text/xpath;
- scroll elements into view;
- enter input text;
- search dynamic company filters.

Developer note: LinkedIn selector drift usually starts here or in `runAiBot.py`. Keep selector changes small and tested manually.

### `modules/validator.py`

Configuration validation.

Responsibilities:

- primitive validators for int, bool, string, list;
- validate each config module;
- enforce allowed values for filters and profile answers;
- run all validation before automation starts.

Maintenance rule: every new config variable should get validation here.

### `modules/ai/`

Optional AI provider support.

- `prompts.py`: prompt templates and JSON response schema for skill extraction and form answers.
- `openaiConnections.py`: OpenAI/OpenAI-compatible client, model listing, chat completion, skills extraction, question answering, placeholder future resume agents.
- `deepseekConnections.py`: DeepSeek client using OpenAI-compatible API, skills extraction, question answering.
- `geminiConnections.py`: Google Gemini client, model listing, completion, skills extraction, question answering.

Known maintenance issue: `validator.py` currently validates `ai_provider` as `openai` or `deepseek`, while README/config/runtime code also mention `gemini`. If Gemini should remain supported, update `validate_secrets()`.

### `modules/resumes/`

Experimental resume support.

- `generator.py`: creates `resume.docx` and `resume.pdf` from structured resume data using `python-docx` and `fpdf`.
- `extractor.py`: placeholder/import-only file.

The main bot currently uploads `default_resume_path`; generated resume flow is not fully wired into `runAiBot.py`.

### `modules/javascript/`

Contains browser-side support scripts.

- `unfollow_companies.js`: helper script for LinkedIn company follow state cleanup/manual automation.

### `modules/images/`

Contains image assets for LinkedIn logo and Easy Apply button detection/reference. Some Easy Apply button images are duplicated under both `modules/images/EasyApplyButton/` and `modules/images/LinkedIn/EasyApplyButton/`.

### `modules/__deprecated__/`

Old setup/config and resume generator code. Do not add new work here unless migrating or deleting deprecated functionality.

## UI Layer

### `templates/index.html`

Single-page applied jobs table.

Responsibilities:

- fetch `http://localhost:5000/applied-jobs`;
- render job title, company, HR contact, external link, and applied status;
- sort by external link;
- call `PUT /applied-jobs/<job_id>` when an external link is clicked.

Maintenance note: the fetch URL is hardcoded to `http://localhost:5000/applied-jobs`. Relative `/applied-jobs` would be more portable if this UI is ever hosted behind another port/proxy.

## Data Outputs

### Applied jobs CSV

Configured by `config/settings.py:file_name`, currently expected by the UI at:

```text
all excels/all_applied_applications_history.csv
```

Columns written by `submitted_jobs()`:

- `Job ID`
- `Title`
- `Company`
- `Work Location`
- `Work Style`
- `About Job`
- `Experience required`
- `Skills required`
- `HR Name`
- `HR Link`
- `Resume`
- `Re-posted`
- `Date Posted`
- `Date Applied`
- `Job Link`
- `External Job link`
- `Questions Found`
- `Connect Request`

### Failed jobs CSV

Configured by `config/settings.py:failed_file_name`:

```text
all excels/all_failed_applications_history.csv
```

Columns written by `failed_job()`:

- `Job ID`
- `Job Link`
- `Resume Tried`
- `Date listed`
- `Date Tried`
- `Assumed Reason`
- `Stack Trace`
- `External Job link`
- `Screenshot Name`

### Logs and screenshots

Configured by `config/settings.py:logs_folder_path`:

```text
logs/log.txt
logs/screenshots/
```

`print_lg()` writes console output and appends to `logs/log.txt`. `screenshot()` writes browser screenshots for failed/manual-intervention cases.

## Setup Scripts

### `setup/windows-setup.bat`

Windows batch setup for ChromeDriver. It requests admin privileges, downloads Chrome-for-Testing metadata, downloads the matching win64 ChromeDriver, extracts it under the Chrome install directory, and starts `chromedriver.exe`.

### `setup/windows-setup.ps1`

PowerShell setup script that checks Python and Chrome, installs Selenium dependencies, downloads ChromeDriver, extracts it, and updates the current process environment.

### `setup/setup.sh`

Shell setup script aimed at a Windows/Git Bash style environment. It checks Python/Chrome, downloads ChromeDriver from Chrome-for-Testing metadata, and installs it under the Chrome directory.

README install command currently lists:

```bash
pip install undetected-chromedriver pyautogui setuptools openai flask-cors flask
```

The source also imports Selenium, Google Gemini, `python-docx`, and `fpdf` in some paths. A future `requirements.txt` would make this easier to maintain.

## Development Workflows

### Add Or Change A Config Variable

1. Add the variable to the correct file under `config/`.
2. Add validation in `modules/validator.py`.
3. Import/use it in the smallest possible runtime module.
4. Update this document and README if the user must configure it.
5. Keep private values out of commits.

### Fix LinkedIn UI Breakage

1. Identify the failing selector from `logs/log.txt` and screenshots.
2. Prefer updating `modules/clickers_and_finders.py` for reusable selector behavior.
3. Update `runAiBot.py` only when the broken selector is specific to one job/application step.
4. Keep old fallback selectors when they still work for other regions/accounts.
5. Test manually with `pause_before_submit = True`.

### Add An AI Provider

1. Add a new provider module under `modules/ai/`.
2. Reuse prompt contracts from `modules/ai/prompts.py`.
3. Add create/extract/answer calls in `runAiBot.py`.
4. Add provider validation in `modules/validator.py`.
5. Add provider config comments in `config/secrets.py`.
6. Avoid logging API keys or full private user context.

### Change CSV Schema

1. Update the writer in `runAiBot.py`.
2. Update `app.py` if the UI consumes the field.
3. Update `templates/index.html` if the displayed model changes.
4. Preserve backward compatibility or add migration handling for old CSV files.
5. Update the Data Outputs section here.

### Change The Flask UI

1. Keep API changes in `app.py`.
2. Keep table/render behavior in `templates/index.html`.
3. Check CSV field names before changing JSON keys.
4. Prefer relative fetch paths if making the UI deployable beyond local Flask.

## Manual Run Commands

Install baseline dependencies:

```bash
pip install selenium undetected-chromedriver pyautogui setuptools openai flask-cors flask
```

Run the bot:

```bash
python runAiBot.py
```

Run the applied jobs UI:

```bash
python app.py
```

Check current Git status:

```bash
git status --short
```

## Maintainability Notes

- There is no test suite in the current repo.
- There is no `requirements.txt` or lock file.
- `modules/open_chrome.py` creates the browser session on import, so importing it in tests/tools has side effects.
- `runAiBot.py` is the largest file and owns many responsibilities. Future refactors should split job search, job extraction, application form handling, CSV persistence, and run orchestration into separate modules.
- `config/personals.py` and `config/secrets.py` contain sensitive/user-specific data. Treat them as local configuration, not source examples.
- `app.py` reads a hardcoded CSV path independent from `config/settings.py`. If output paths become configurable for the UI, wire `app.py` to the same config source.
- `modules/ai/openaiConnections.py` contains duplicate `ai_evaluate_resume()` stubs and several future-agent `pass` placeholders.
- `config/resume.py`, `modules/resumes/extractor.py`, and parts of resume generation are not active in the main application path.
- `ai_provider = "gemini"` is present in runtime code/config comments, but validator support is incomplete.

## Ownership Boundaries

- Bot behavior: `runAiBot.py`, `modules/helpers.py`, `modules/clickers_and_finders.py`, `modules/open_chrome.py`.
- User configuration: `config/*.py`.
- Config validation: `modules/validator.py`.
- AI behavior: `modules/ai/*.py`.
- Applied jobs UI: `app.py`, `templates/index.html`.
- Resume generation experiments: `modules/resumes/*.py`, `config/resume.py`.
- Setup/ChromeDriver installation: `setup/*`.
- Runtime state: `all excels/`, `all resumes/`, `logs/`.

