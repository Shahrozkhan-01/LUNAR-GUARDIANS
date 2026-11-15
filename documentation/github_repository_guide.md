# Public GitHub Repository Guide

## Repository structure

```text
backend/             FastAPI application, services, models, and tests
frontend/            React/Vite application, styles, assets, and browser UI
datasets/             NASA source products, processed products, metadata, scripts
documentation/        Requirements, architecture, science, testing, and screenshots
README.md             Setup, project overview, limitations, and publication notes
start-lunar-guardians.ps1
                      Windows launcher for the local backend and frontend
```

The backend owns mission state and NASA API access. The frontend calls the
backend and never receives the NASA API key.

## Files included in normal Git publication

- Application source under `backend/app/` and `frontend/src/`.
- Backend tests and dependency manifests.
- Frontend assets, package metadata, and public UI assets.
- Documentation, validation reports, dataset metadata, processing scripts,
  summaries, and genuine screenshots.
- `.env.example` with placeholder values only.

## Files excluded

The root `.gitignore` excludes:

- `backend/.env` and other environment files.
- Python virtual environments, caches, `__pycache__`, and bytecode.
- `frontend/node_modules`, build output, and local tool caches.
- Logs, coverage output, editor files, and temporary files.
- All local `datasets/raw/` and `datasets/processed/` products by default.

The excluded dataset files are not deleted. They remain in the local project
workspace and are described by metadata and processing documentation. An owner
may explicitly stage an approved product only after checking its terms,
attribution, hosting, and size.

## Dataset hosting strategy

Before creating a public repository, choose one of these approaches for the
two oversized products:

1. Store approved products with Git LFS and verify the university/public
   repository quota.
2. Host them in an approved NASA or university archive and document a
   reproducible download step.
3. Publish the project without dataset products and clearly label the affected
   dataset views as unavailable in a fresh clone.

Do not silently replace products with fabricated data or claim that a normal
GitHub clone contains files that are hosted elsewhere. Keep metadata, source
URLs, validation reports, and processing scripts in Git.

## Environment setup for judges

From Windows PowerShell:

```powershell
cd D:\NASA\LUNAR-GUARDIANS
Copy-Item backend\.env.example backend\.env
notepad backend\.env

cd backend
py -3 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt

cd ..\frontend
npm install
cd ..
.\start-lunar-guardians.ps1
```

The local `backend/.env` may contain a personal NASA key, but it must never be
committed. `DEMO_KEY` is acceptable for a basic demonstration and is
rate-limited.

## Running and testing

The launcher starts FastAPI at `http://127.0.0.1:8000` and Vite at
`http://127.0.0.1:5173`. Manual startup commands and the complete test
commands are in [README.md](../README.md).

Verified baseline before publication preparation:

- Backend: 49 tests passed.
- Frontend lint: passed.
- Frontend production build: passed, with a non-blocking Vite chunk advisory.

## Security considerations

- Never put NASA keys in React code, screenshots, documentation, or commits.
- Review `git status`, `git ls-files`, and `git check-ignore` before staging.
- Do not stage `backend/.env`, `venv`, `node_modules`, caches, logs, or build
  output.
- Do not publish personal information, local paths that reveal private data,
  browser profiles, or terminal output containing secrets.

## License and NASA attribution

No project license file is currently present. The project owner retains
copyright by default, so public visibility does not automatically grant reuse
permission. The owner should choose and add an appropriate project license
before publication if reuse is desired.

NASA dataset source organizations, source URLs, acquisition methods,
processing, validation, and limitations are documented in
[NASA data sources and validation](nasa_data_sources_and_validation.md).
Review the applicable NASA, PDS, CDAWeb, instrument-team, and JPL Horizons
terms before redistributing source products.

## Known limitations

- Mission state is in memory and is lost when FastAPI restarts.
- DONKI depends on NASA availability and rate limits.
- Two large dataset products need Git LFS or alternative hosting.
- The frontend production build has a non-blocking large-chunk advisory.
- Browser automation cannot prove physical speaker output.
