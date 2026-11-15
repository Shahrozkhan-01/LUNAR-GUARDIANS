# Optional free deployment: Vercel + Render

This guide deploys the React/Vite website to Vercel and the existing FastAPI
backend to Render's **Free** web-service plan. A public frontend alone cannot
run the complete game: the browser needs a public backend URL for missions,
NASA event requests, and dataset APIs.

The application remains runnable locally with `.\start-lunar-guardians.ps1`.
Hosting is optional.

## Before starting

- Push the current project to the existing GitHub repository:
  <https://github.com/Shahrozkhan-01/LUNAR-GUARDIANS>.
- Create/sign into Vercel and Render using your own accounts. Keep both services
  on free plans. Do not add a payment method, enable paid usage, or accept an
  upgrade. If a screen requires payment or a paid upgrade, stop.
- Use the existing repository. Do not create another repository.

## Step 1: Deploy the frontend on Vercel

1. In Vercel, choose **Add New → Project** and import
   `Shahrozkhan-01/LUNAR-GUARDIANS`.
2. In project settings, set **Root Directory** to `frontend`.
3. Use these build settings (Vercel normally detects Vite automatically):
   - Framework preset: **Vite**
   - Build command: `npm run build`
   - Output directory: `dist`
   - Install command: `npm ci`
4. Deploy. Record the production origin Vercel assigns, for example
   `https://your-project.vercel.app` (no trailing slash).
5. The frontend may show backend connection errors until the backend has been
   deployed and its URL is configured in Step 3. This initial deploy is only to
   establish the Vercel project/domain.

`frontend/vercel.json` routes browser paths such as `/mission-control` to the
React app so reloading a game page does not produce a Vercel 404.

## Step 2: Deploy the backend on Render Free

1. In Render, choose **New → Blueprint** and connect the same existing GitHub
   repository.
2. Confirm that Render reads the root-level `render.yaml`.
3. Before creating the service, check the plan shown for
   `lunar-guardians-api`; it must say **Free**. Stop if Render requests a paid
   plan or payment details.
4. When prompted for `FRONTEND_URL`, enter the exact Vercel production origin
   from Step 1, for example `https://your-project.vercel.app`, with no trailing
   slash. For additional Vercel preview domains, add exact origins separated by
   commas.
5. Create and wait for the service to finish deploying. The blueprint uses
   `DEMO_KEY` for NASA requests; it is rate-limited but does not require adding
   a personal key. The key is used by the backend, not exposed to React.
6. Copy the Render service's public base URL, for example
   `https://lunar-guardians-api.onrender.com` (no trailing slash).

Check that these URLs return successfully:

- `https://YOUR-RENDER-SERVICE.onrender.com/health` → `{"status":"ok"}`
- `https://YOUR-RENDER-SERVICE.onrender.com/api/datasets`
- `https://YOUR-RENDER-SERVICE.onrender.com/docs`

The Render free service can sleep after inactivity and take time to wake when
first opened. It has limited monthly free usage; do not enable paid usage.

## Step 3: Connect Vercel to Render

1. In Vercel, open the project **Settings → Environment Variables**.
2. Add:
   - **Name:** `VITE_API_BASE_URL`
   - **Value:** your Render backend base URL, such as
     `https://lunar-guardians-api.onrender.com`
   - **Environments:** Production (and Preview if you want preview deployments
     to use the same backend).
3. Save, then open **Deployments** and redeploy the latest production
   deployment so Vite builds the frontend with the new variable.
4. Check Render's `FRONTEND_URL` is the exact production Vercel origin. Update
   it in the Render dashboard if your Vercel domain differs from the value used
   at service creation, then redeploy/restart the Render service.

`VITE_API_BASE_URL` is a public service URL, not a secret. Never put
`NASA_API_KEY` in Vercel or in a `VITE_` variable. `NASA_API_KEY` belongs only
in the Render backend environment if you later choose to use a personal key.

## Step 4: Test the public game

Open the Vercel production URL and verify:

1. The landing page loads, including images and styling.
2. Mission Setup loads and a mission starts.
3. Mission Control actions and advancing a day work.
4. The mission can complete and the debrief appears.
5. NASA Data Explorer loads `/api/datasets` and dataset metadata.
6. DONKI status either displays live data or clearly reports temporary
   unavailability; NASA outages must not prevent ordinary gameplay.
7. Refreshing `/mission-control` or `/nasa-data` loads the React app.
8. The browser console has no blocking errors.

The Render free service may be sleeping when its first request is made. Wait
for it to wake before treating the first slow request as a failure.

## Free-plan and feature limitations

- Keep Render's instance plan set to **Free** and Vercel on its free Hobby
  offering if eligible. Do not enter payment details or enable paid usage.
- Render's Free web service sleeps after inactivity. First requests after sleep
  can be slow.
- The backend keeps active missions in memory; they are not saved across
  backend restarts or sleeps.
- NASA DONKI uses the shared `DEMO_KEY` by default and is subject to rate
  limits. An unavailable feed is reported and does not create fake events.
- A free host can change its limits or terms. Check the plan and billing page
  before confirming service creation; stop if paid usage is required.
- Deploying code does not guarantee independent NASA science certification or
  NASA endorsement.

## Troubleshooting

| Symptom | Check |
|---|---|
| Browser says it cannot reach Mission Control | `VITE_API_BASE_URL` is set to the Render service origin and Vercel was redeployed after changing it. |
| Browser reports CORS | Render `FRONTEND_URL` exactly matches the Vercel origin, including `https://` and excluding a trailing slash. |
| Render deploy fails | Review Render build logs; the backend root directory must be `backend`, and requirements install with `pip install -r requirements.txt`. |
| First API request is slow | The Render Free service may be waking from sleep; wait and retry. |
| Dataset says unavailable | Check that the selected product file exists in the deployed repository and inspect `/api/datasets` availability. Never replace missing NASA data with fabricated values. |
| Direct refresh of a frontend route returns 404 | Confirm `frontend/vercel.json` is present and Vercel Root Directory is `frontend`, then redeploy. |

## Official host documentation

- [Vercel project configuration](https://vercel.com/docs/project-configuration/vercel-json)
- [Vercel build configuration](https://vercel.com/docs/deployments/configure-a-build)
- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
- [Render Python version configuration](https://render.com/docs/python-version)
- [Render Free instance plans and limitations](https://render.com/docs/free)
