# GitHub Public-Repository Publication Checklist

## Security audit

- [x] `backend/.env` is ignored.
- [x] `.env.example` contains only the `DEMO_KEY` placeholder and configuration
      names; no personal credential was included in the repository.
- [x] Python virtual environments, `node_modules`, bytecode, caches, logs,
      build output, and temporary files are ignored.
- [x] Source scan found no personal API key, password, private key, or bearer
      credential.
- [x] NASA keys remain backend-only and are not exposed to React.
- [ ] Before staging, manually inspect `git diff --cached` for secrets.

## Dataset size report

The audit excluded local virtual-environment and `node_modules` contents from
the publication-size calculation. Two project dataset files exceed GitHub's
100 MB individual-file limit:

| File | Approximate size | Publication status |
|---|---:|---|
| `datasets/raw/lunar_environment/diviner/global_cumul_avg_cyl_80s70s_002.tab` | 148.97 MB | Git LFS or external archive required |
| `datasets/processed/lunar_environment/lola/ldem_16_processed.npz` | 101.49 MB | Git LFS or external archive required |

No other file in the audited project tree exceeded 50 MB. All raw and
processed NASA products are now ignored by default to prevent accidental
publication before terms and hosting are approved. The products were not
deleted or modified. Their metadata, summaries, source references, validation
material, and processing scripts remain available for inspection.

## Files to include

- `backend/app/`, `backend/tests/`, `backend/requirements.txt`, and
  `backend/.env.example`.
- `frontend/src/`, `frontend/public/`, `frontend/package.json`, and
  `frontend/package-lock.json` if present.
- `datasets/metadata/`, validation reports, processing scripts, and
  documentation about raw/processed products.
- `documentation/`, including screenshots and this checklist.
- `README.md`, `.gitignore`, and `start-lunar-guardians.ps1`.

## Files to exclude

- `backend/.env`
- `backend/venv/`, `venv/`, `.venv/`
- `frontend/node_modules/`
- `__pycache__/`, `*.pyc`, and tool caches
- `frontend/dist/`, build output, logs, coverage, and temporary files
- `datasets/raw/` and `datasets/processed/` unless an owner explicitly
  approves a product after terms and hosting review.

## README and documentation

- [x] Root README updated for judges with setup, architecture, datasets,
      screenshots, tests, limitations, and future improvements.
- [x] Public repository guide created.
- [x] Documentation index links to the publication checklist.
- [x] All checked Markdown links resolve.
- [x] Dataset attribution and scientific limitations are documented.

## License status

No project `LICENSE` file was found. Do not claim that the project is
open-source or assign a license without the owner's authorization. The owner
must choose a project license before publication if reuse permissions are
intended. NASA and third-party dataset terms must be reviewed independently.

## Git status

- Git is already initialized.
- One initial commit exists.
- The complete implementation and documentation are currently in the working
  tree as staged/uncommitted preparation work; no commit or push was performed
  during this audit.
- Confirm ignored files with:

```powershell
git check-ignore -v backend/.env backend/venv frontend/node_modules
git ls-files
git status --short
```

## Manual actions before publication

1. Decide whether to use Git LFS or an approved external archive for the two
   oversized NASA products.
2. Review NASA/PDS/CDAWeb/instrument-team/JPL terms for any exact files being
   redistributed, then explicitly stage only approved products.
3. Choose and add a project license if reuse is intended.
4. Review the complete staged diff for secrets and private information.
5. Test a clean clone using only the files intended for publication.
6. Add the GitHub remote only after review.
7. Commit and push only after explicit owner confirmation.

This audit intentionally did not create a remote, commit changes, push to
GitHub, or make the repository public.
