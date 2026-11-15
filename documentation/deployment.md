# Free public deployment

The project uses the existing GitHub repository
`Shahrozkhan-01/LUNAR-GUARDIANS`, GitHub Pages for the React/Vite frontend, and
Render Free for FastAPI.

## GitHub Pages

- Public URL: <https://shahrozkhan-01.github.io/LUNAR-GUARDIANS/>
- The Actions workflow builds from `frontend/` and deploys on pushes to `main`.
- In repository settings, enable Pages with **Build and deployment → Source →
  GitHub Actions**.
- The production Vite base path is `/LUNAR-GUARDIANS/`; the build includes
  `404.html` as a fallback for client-side routes.
- Set the Actions repository variable `VITE_API_BASE_URL` to the actual Render
  service URL if it differs from the workflow's default.

## Render Free

- Blueprint: [render.yaml](../render.yaml), explicitly configured with
  `plan: free`.
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`
- `NASA_API_KEY`: set as a Render secret. `DEMO_KEY` may be used, but has lower
  rate limits.
- `FRONTEND_URL`: preconfigured to `https://shahrozkhan-01.github.io`.

Initial GitHub Pages and Render service setup requires dashboard authorization.
If any dashboard requests payment details or a paid upgrade, stop; use only the
free plan.

Large Diviner and LOLA files are not committed because of GitHub's 100 MB
individual-file limit. Upload them to the GitHub Release named `datasets-v1`
using [dataset_download_manifest.json](../datasets/dataset_download_manifest.json)
and verify the SHA-256 values before deployment. The backend preserves explicit
dataset-unavailable responses if a release asset is not present; it never
fabricates records.
