# Conduital — Windows MVP Distribution Checklist

**Goal:** Package Conduital as a Windows desktop product and sell via Gumroad.
**Target Timeline:** 4–6 weeks (part-time)
**Last Updated:** February 8, 2026

---

## Phase 0 — Security & Hygiene (BLOCKER — Do First)

### 0.1 Revoke Exposed API Key
- [ x] Log into Anthropic Console and revoke the compromised API key immediately
- [x ] Generate a new API key for personal development use
- [x ] Confirm the old key no longer works by testing a request against it

### 0.2 Purge Secrets from Repository
- [x] Delete `backend/Anthropic API Key.txt` from the working tree *(done 2026-02-07 — file was already gitignored, never tracked)*
- [ ] Remove the file from full Git history using BFG Repo Cleaner or `git filter-branch` *(N/A if never pushed to remote)*
- [x] Audit `backend/.env` — confirm it is not committed to the repo *(verified: properly gitignored)*
- [x] Search entire codebase for any other hardcoded secrets, API keys, or tokens *(done 2026-02-07 — no sk-ant keys in code, all password/secret refs are config variables)*
- [ ] If repo has been pushed to any remote (GitHub, etc.), force-push the cleaned history and rotate all credentials

### 0.3 Remove Hardcoded Paths
- [x] Remove `SECOND_BRAIN_ROOT=G:/My Drive/...` from any committed files *(done 2026-02-07 — cleaned 22 files, replaced with generic placeholders)*
- [x] Audit codebase for any other user-specific paths *(done 2026-02-07 — no G:/ or C:/Users paths remain outside meta-references in distribution-checklist.md)*
- [x] Create `backend/.env.example` with placeholder values and comments explaining each variable *(existed since initial commit; paths + version updated 2026-02-07)*
- [x] Document all required and optional environment variables in `.env.example` *(215 lines covering all 30+ variables with descriptions)*

### 0.4 Set Up Proper .gitignore
- [x] Add/verify `.gitignore` covers: *(comprehensive .gitignore committed in initial commit)*
  - [x] `.env` (all directories)
  - [x] `*.db` and `*.db-wal` and `*.db-shm` (SQLite files)
  - [x] `logs/`
  - [x] `__pycache__/` and `*.pyc`
  - [x] `node_modules/`
  - [x] `frontend/dist/` (build output)
  - [x] `dist/` and `build/` (PyInstaller output)
  - [x] `*.spec` (PyInstaller spec files, optional)
  - [x] Any IDE-specific folders (`.vscode/`, `.idea/`)
  - [x] API key files (`**/Anthropic API Key*`, `**/API Key*`, `**/credentials*`, `**/secrets*`)
  - [x] Certificate files (`*.key`, `*.pem`, `*.cert`)
- [x] Run `git status` to confirm no sensitive files are tracked *(verified 2026-02-07)*

### 0.5 Fix JWT Secret Handling
- [x] Review `backend/app/core/config.py` — understand current default behavior *(done 2026-02-07)*
- [x] Implement auto-generation of a strong JWT secret on first run *(done 2026-02-07 — `_get_or_generate_secret_key()` uses `secrets.token_urlsafe(64)`)*
- [x] Ensure the generated secret persists across app restarts *(persists to .env file automatically)*
- [x] Remove any weak default secret from the codebase *(replaced with auto-generated key)*

### 0.6 Product Naming & Branding *(decisions made 2026-02-07)*
- [x] Brainstorm product name candidates *(11 candidates researched across 2 rounds)*
- [x] Research name uniqueness: *(all 11 candidates verified with actual searches, not just AI estimates)*
  - [x] Web search for existing products with the same or confusingly similar names
  - [x] Search major app stores (Microsoft Store, Google Play, Apple App Store)
  - [x] Search Gumroad for similar product names
  - [x] Check domain availability (`.com`, `.io`, `.app`)
  - [x] Search USPTO trademark database (https://tmsearch.uspto.gov)
  - [x] Search GitHub / open-source projects for name collisions
  - [x] Search social media handles availability (Twitter/X, Reddit, etc.)
- [x] Evaluate final candidates against criteria:
  - [x] Memorable and easy to spell
  - [x] No confusion with established productivity tools (Todoist, Things, Notion, etc.)
  - [x] No trademark conflicts
  - [x] Domain available (or acceptable alternative)
- [x] Decide on final product name: **Conduital**
  - Etymology: Conduit + -al ("of or relating to a conduit")
  - conduital.com PURCHASED ✅, conduital.io AVAILABLE, conduital.app AVAILABLE ($19.99)
  - USPTO: ZERO results (no live or dead filings)
  - GitHub @conduital: CLAIMED ✅ (gregdm98607/conduital)
  - Twitter/X @conduital: CLAIMED ✅
  - Gumroad: CLAIMED ✅
  - Risk level: LOW — complete blank slate
  - Key eliminated candidates: Operaxis (active US tech company), Velocient (.com blocked), Moventis (Spanish transport giant), Kinetic (Epicor + productivity app), all others HIGH risk
- [x] Decide on product name representation in the app:
  - [x] Typography treatment: **Conduital** (Title case, clean and professional)
  - [x] Where the name appears: title bar, sidebar header, login/splash screen, About page
  - [x] Tagline / subtitle: **"The Conduit for Intelligent Momentum"**
- [x] Decide on logo:
  - [x] Wordmark only for now (styled product name as logo). Icon mark deferred to pre-distribution.
  - [ ] Design or commission the icon mark *(deferred — do before Phase 5)*
  - [ ] Create icon variants for all required contexts:
    - [ ] Windows app icon (`.ico`, multiple sizes: 16x16 through 256x256)
    - [ ] System tray icon (16x16 and 32x32)
    - [ ] Installer header/banner image
    - [ ] Gumroad product cover image
    - [ ] Favicon for browser tab
  - [ ] Ensure logo works at small sizes and in both light/dark contexts
- [x] Update all references from "Project Tracker" to "Conduital" across the codebase *(done 2026-02-07 — 56 occurrences updated across frontend, backend, config, and export files)*

---

## Phase 1 — Architecture Adjustments for Distribution

### 1.1 Eliminate Node.js Runtime Requirement for End Users
- [x] Confirm `npm run build` (Vite) produces a complete static build in `frontend/dist/` *(verified 2026-02-07)*
- [x] Configure FastAPI to serve the static frontend files: *(done 2026-02-07 — added to main.py)*
  - [x] Mount `StaticFiles` for the built assets directory
  - [x] Add a catch-all route that serves `index.html` for client-side routing
- [x] Test the full app running with only the Python backend (no `npm run dev`) *(verified 2026-02-07 — health, root SPA, /projects, static JS, API, /docs all return 200)*
- [x] Verify all frontend routes, API calls, and assets load correctly from the static build *(verified 2026-02-07 — 6/6 endpoint checks pass; fixed root "/" to serve SPA when build exists)*
- [x] Update `vite.config.ts` if needed to set correct `base` path for production *(N/A — default "/" is correct)*

### 1.2 Auto-Run Database Migrations on Startup
- [x] Wire Alembic `upgrade head` into the FastAPI startup lifecycle event *(done 2026-02-07 — `run_migrations()` in lifespan)*
- [x] Handle the case where the database file doesn't exist yet (first run) — create the directory and file *(done — `db_dir.mkdir(parents=True, exist_ok=True)` in lifespan)*
- [x] Handle the case where migrations are already current (no-op, no errors) *(Alembic handles this natively)*
- [x] Test upgrading from an empty state to fully migrated *(verified 2026-02-07 — 12 migrations, 17 tables, user_id columns present; fixed repair migration 010 to check column existence before adding)*
- [ ] Test upgrading from a mid-point (simulating an app update with new migrations)
- [x] Add error handling and logging for migration failures *(done — try/except with fallback to create_all)*

### 1.3 Define User Data Directory *(completed 2026-02-08)*
- [x] Choose a standard Windows location for app data (e.g., `%LOCALAPPDATA%\Conduital\`) *(done — `backend/app/core/paths.py` created as single source of truth)*
- [x] Store the following in this directory:
  - [x] SQLite database file (`tracker.db`) *(packaged mode: `%LOCALAPPDATA%\Conduital\tracker.db`)*
  - [x] Generated JWT secret *(persisted to config.env in data dir)*
  - [x] User configuration / settings file (replaces `.env` for end users) *(packaged: `config.env`)*
  - [x] Log files *(packaged: `%LOCALAPPDATA%\Conduital\logs\`)*
- [x] Create the directory automatically on first run if it doesn't exist *(`ensure_data_dir()` creates data, logs, backups subdirs)*
- [x] Ensure all file paths in the app reference this directory dynamically (no hardcoding) *(all paths resolved via `paths.py`; dev mode unchanged, 174/174 tests pass)*

### 1.4 Build First-Run Setup Wizard *(completed 2026-02-08)*
- [x] Design a setup flow as a page/modal in the React frontend *(4-step wizard in `SetupWizard.tsx`)*
- [x] Step 1: Welcome screen explaining what the app does *(includes data directory info, legacy migration option)*
- [x] Step 2: Sync folder selection
  - [x] Implement a folder picker (either native dialog via API endpoint or manual path entry) *(manual path entry with Validate button)*
  - [x] Validate the selected path exists and is accessible *(`POST /setup/validate-path` endpoint)*
  - [x] Explain what the app will do with this folder *(descriptive text in wizard step)*
  - [x] Allow skipping (sync features disabled) *(skip option on each step)*
- [x] Step 3: Anthropic API key (optional)
  - [x] Text input with paste support *(password-type input with show/hide toggle)*
  - [x] "Test Connection" button that validates the key via API call *(reuses `/ai/test` endpoint)*
  - [x] Clear messaging: "AI features are optional. Without a key, all other features work normally." *(included)*
  - [x] Link to Anthropic's signup page for users who don't have a key *(link to console.anthropic.com)*
  - [x] Explain that usage costs are between the user and Anthropic *(noted in wizard text)*
- [x] Step 4: Confirmation / "Get Started" screen *(summary of all choices with Launch button)*
- [x] Save all configuration to the user data directory *(`POST /setup/complete` persists to config file)*
- [x] Add a flag/marker so the wizard only shows on first run *(`SETUP_COMPLETE=true` in config; `SetupGuard.tsx` checks on mount)*
- [x] Provide a way to re-run setup or edit settings later from within the app *(Settings page "System Setup" section with "Re-run Setup Wizard" button)*

### 1.5 Verify Graceful AI Degradation
- [x] Launch the app with no Anthropic API key configured *(verified 2026-02-07 — AI_FEATURES_ENABLED=false, key empty)*
- [x] Test every AI-powered feature and confirm: *(verified 2026-02-07 — code audit + functional test)*
  - [x] No unhandled exceptions or crashes *(create_provider raises clean ValueError; endpoints return HTTP 400 with message)*
  - [x] UI elements for AI features show a clear "requires API key" or "set up in settings" state *(Settings page shows "Not set" badge with WifiOff icon)*
  - [x] Non-AI features all function normally *(momentum scoring, project health, discovery all work without key)*
- [x] Test with an invalid API key — confirm helpful error message, not a stack trace *(verified: /ai/test returns `{success: false, message: "..."}` with Pydantic response model)*
- [ ] Test with a valid key that has exceeded its quota — confirm graceful handling *(requires intentional quota exhaustion — deferred)*

### 1.6 Single-Process Launch Architecture
- [x] Create a Python entry point script *(done 2026-02-07 — `backend/run.py`)*
  - [x] Checks if first run → triggers setup wizard *(done 2026-02-08 — `SetupGuard` redirects to `/setup` in packaged mode)*
  - [x] Runs Alembic migrations *(handled by lifespan in main.py)*
  - [x] Starts Uvicorn serving the FastAPI app (which includes static frontend)
  - [x] Opens the user's default browser to `http://localhost:<PORT>`
  - [x] Handles clean shutdown *(KeyboardInterrupt + signal handling)*
- [x] Choose a default port *(52140 — unlikely to conflict)*
- [x] Implement port conflict detection: check if port is in use, increment if necessary *(find_available_port())*
- [x] Store the active port so the browser opens to the correct URL

---

## Phase 2 — PyInstaller Packaging *(core build completed 2026-02-08)*

### 2.1 Initial PyInstaller Setup *(completed 2026-02-08)*
- [x] Install PyInstaller in the project (`pip install pyinstaller`) *(added to dev dependencies in requirements.txt + pyproject.toml)*
- [x] Create an initial `.spec` file *(hand-written `backend/conduital.spec` with comprehensive config)*
- [x] Configure the `.spec` file:
  - [x] Add `frontend/dist/` as a data directory (the built static files) *(bundled as `frontend_dist/`)*
  - [x] Add Alembic migration files as data *(bundled as `alembic/`)*
  - [x] Add `alembic.ini` as data *(bundled at root)*
  - [x] Add any other non-Python assets (templates, default configs) *(assets dir bundled if present)*
  - [x] Set the application icon (`.ico` file) *(configured, uses `assets/conduital.ico` when available)*
- [x] Create `backend/version_info.txt` — Windows exe metadata *(CompanyName, ProductName, FileDescription, ProductVersion)*
- [x] Create `build.bat` — automated build script *(frontend build + PyInstaller, supports --skip-fe and --clean flags)*

### 2.2 Resolve Packaging Issues *(completed 2026-02-08)*
- [x] Run the first build and catalog all errors *(first build succeeded after path fix in spec file)*
- [x] Handle hidden imports — FastAPI, SQLAlchemy, and Pydantic often need explicit imports listed:
  - [x] `uvicorn.logging` *(included)*
  - [x] `uvicorn.loops.auto` *(included with all uvicorn internals)*
  - [x] `uvicorn.protocols.http.auto` *(included)*
  - [x] SQLAlchemy dialect imports *(sqlalchemy.dialects.sqlite included)*
  - [x] Pydantic internal modules *(pydantic, pydantic.fields, pydantic_settings included)*
  - [x] Any other modules PyInstaller fails to detect *(70+ hidden imports specified covering all dependencies)*
- [x] Handle native extensions:
  - [x] `python-jose[cryptography]` — ensure cryptography wheels are bundled *(PyInstaller hook handles automatically)*
  - [x] `watchdog` — included with events + observers *(hidden imports specified)*
  - [x] `uvicorn[standard]` — included with all protocol backends *(h11 + httptools + wsproto)*
- [x] Verify the bundled SQLite works correctly *(sqlite3 hook included by PyInstaller)*

### 2.3 System Tray Integration *(completed 2026-02-08)*
- [x] Add `pystray` (or similar) as a dependency *(pystray + Pillow added to requirements.txt + pyproject.toml)*
- [x] Create a system tray icon with menu: *(backend/app/tray.py)*
  - [x] "Open Conduital" — opens/focuses the browser tab *(default action)*
  - [x] "Settings" — opens settings page in browser
  - [x] Separator
  - [x] Version info (disabled menu item)
  - [x] "Quit" — cleanly shuts down the server and exits *(signals shutdown_event)*
- [x] Icon loading: tries bundled .ico, project assets, then generates placeholder *(PIL-based blue "C" square)*
- [x] Ensure the app runs as a tray application (no visible console window) *(console=False in spec, run_packaged() in run.py)*
- [x] Handle the case where the user closes the browser tab — tray icon persists, re-openable *(tray persists independently)*
- [x] Graceful fallback if pystray not available *(import guarded with try/except)*

### 2.4 Build & Test Cycle *(build verified 2026-02-08; dev machine testing PASSED 2026-02-08)*
- [x] Build the full package with PyInstaller *(successful build, ~66 MB output)*
- [x] Test on your development machine — confirm everything works *(13/13 tests pass — launch, migrations, server, browser, setup wizard, SPA routes, static assets, API, data dir, logs, tray, shutdown, persistence)*
- [ ] **Test on a clean Windows 10 VM** (no Python, no Node.js installed):
  - [ ] Does the app launch?
  - [ ] Does the browser open correctly?
  - [ ] Does first-run setup work?
  - [ ] Do all features function (minus AI if no key)?
  - [ ] Does the system tray icon appear and work?
  - [ ] Does the app shut down cleanly?
- [ ] **Test on a clean Windows 11 VM** — repeat all above
- [x] Note and fix any missing DLLs, import errors, or path issues *(none found on dev machine)*
- [x] Check the final package size — aim for reasonable (under 100–150 MB ideally) *(~66 MB — well under target)*
- [x] Test startup time — should feel responsive (under 5–10 seconds to browser open) *(server responds within ~3s, browser opens at ~4s)*

---

## Phase 3 — Installer & Code Signing

### 3.1 Code Signing Certificate
- [ ] Research certificate providers (DigiCert, Sectigo, SSL.com)
- [ ] Decide: Standard vs. EV (Extended Validation) certificate
  - Standard (~$200–300/year): Works but requires SmartScreen reputation building
  - EV (~$400–500/year): Immediate SmartScreen trust, recommended for paid software
- [ ] Purchase the certificate
- [ ] Set up signing tools (`signtool.exe` from Windows SDK)
- [ ] Sign the main `.exe` with the certificate
- [ ] Verify the signature (`signtool verify /pa Conduital.exe`)

### 3.2 Create Installer with Inno Setup *(completed 2026-02-08)*
- [x] Download and install Inno Setup *(Inno Setup 6.7.0 installed via winget)*
- [x] Create the installer script (`.iss` file) covering: *(`installer/conduital.iss`)*
  - [x] App name, version, publisher info *(Conduital, 1.0.0-alpha, Conduital)*
  - [x] Installation directory (default: `C:\Program Files\Conduital\`) *(`{autopf}\Conduital`)*
  - [x] All files from the PyInstaller output *(exe + `_internal\*` recursive)*
  - [x] Start Menu shortcut creation *(app + uninstaller shortcuts)*
  - [x] Optional Desktop shortcut *(unchecked by default)*
  - [x] Uninstaller registration in Windows "Apps & Features" *(automatic with Inno Setup)*
  - [ ] Application icon *(configured but icon file not yet created — uses default until `assets/conduital.ico` exists)*
  - [x] License agreement screen (display EULA during install) *(LICENSE file)*
  - [x] Optional: "Launch Conduital" checkbox on final screen *(postinstall nowait)*
- [x] Build the installer *(29 MB output: `installer/Output/ConduitalSetup-1.0.0-alpha.exe`)*
- [ ] Sign the installer `.exe` with the code signing certificate *(deferred — shipping without signing for alpha)*
- [x] Test the full install → launch → use → uninstall cycle on dev machine: *(PASS — all steps verified 2026-02-08)*
- [ ] Test on clean VMs:
  - [ ] Windows 10 VM
  - [ ] Windows 11 VM
- [x] Verify uninstaller removes all files from Program Files *(verified — `C:\Program Files\Conduital\` fully cleaned)*
- [x] Decide: should uninstall remove user data (`%LOCALAPPDATA%\Conduital\`) or leave it? *(leave by default; custom Pascal code prompts user with option to remove, default is No)*

### 3.3 Version Management
- [x] Establish a versioning scheme *(SemVer per STRAT-008: Major.Minor.Patch)*
- [x] Set version number in: *(set to 1.0.0-alpha on 2026-02-07)*
  - [x] Python package config (`backend/pyproject.toml`)
  - [x] Frontend `package.json`
  - [x] Backend config (`backend/app/core/config.py`)
  - [x] `.env.example`
  - [x] PyInstaller `.spec` file *(done 2026-02-08 — version read from config at build time)*
  - [x] Inno Setup `.iss` file *(done 2026-02-08 — `#define MyAppVersion "1.0.0-alpha"` in `installer/conduital.iss`)*
- [ ] Consider a single source of truth for version number (one file read by all)

---

## Phase 4 — Licensing, Legal & Compliance

### 4.1 License Key System (Gumroad Integration) *(DEFERRED — shipping free alpha per STRAT-009)*
> **Decision:** Ship free alpha without license keys to get early users and feedback.
> Implement Gumroad license validation before transitioning to paid beta.
> Step-by-step implementation guide: `tasks/gumroad-license-guide.md`

- [ ] Review Gumroad's license key API documentation
- [ ] Implement license validation in the app:
  - [ ] On first launch (after setup wizard): prompt for license key
  - [ ] Call Gumroad's API to validate the key
  - [ ] Decide on validation policy:
    - Online-only (requires internet each launch)? Or,
    - Validate once, store locally, periodic re-validation? (Recommended for MVP)
  - [ ] Store validation status securely in user data directory
  - [ ] Handle: invalid key, expired key, network failure during validation
- [ ] Decide how many activations per key (Gumroad supports this)
- [ ] Build a "Enter License Key" screen in the app UI
- [ ] Provide a way to enter/change the key later (in settings)
- [ ] Consider a trial period or limited free version to reduce purchase friction

### 4.2 EULA (End User License Agreement) *(completed 2026-02-08)*
- [x] Draft or have drafted a EULA covering: *(LICENSE file — 10 sections, 200+ lines)*
  - [x] License grant (what the user is allowed to do) *(Section 2: 3 devices, personal/business use)*
  - [x] Number of devices / installations allowed *(3 devices per user)*
  - [x] Restrictions (no reverse engineering, redistribution, etc.) *(Section 3: 6 restrictions)*
  - [x] AI features disclaimer: user provides their own Anthropic API key; usage costs are theirs; Anthropic's terms apply *(Section 4c: detailed AI data handling)*
  - [x] Data handling: all data stored locally on user's machine; app does not transmit user data to the developer *(Section 4: local storage, file sync, AI, no telemetry)*
  - [x] No warranty / limitation of liability *(Sections 7-8: AS-IS, AI output disclaimer, aggregate cap)*
  - [x] Termination conditions *(Section 9: breach termination, data ownership survives)*
- [ ] Have the EULA reviewed (ideally by a lawyer, at minimum by an AI legal review)
- [x] Embed EULA in the installer (displayed during installation) *(installer/conduital.iss LicenseFile=..\LICENSE)*
- [x] Make EULA accessible within the app (About/Legal section) *(/api/v1/legal/eula + /api/v1/legal/third-party endpoints added to main.py)*

### 4.3 Privacy Policy
- [ ] Draft a privacy policy covering:
  - [ ] What data the app collects (local database contents)
  - [ ] What data is transmitted externally:
    - Gumroad license validation (license key sent to Gumroad)
    - Anthropic API calls (user's data sent to Anthropic when using AI features, under user's own API key)
    - Any analytics or telemetry (if implemented; recommend none for MVP)
  - [ ] Data storage: all local, user controls their own data
  - [ ] Third-party services and their privacy policies (link to Anthropic's, Gumroad's)
- [ ] Host the privacy policy on a webpage (can be a simple GitHub Pages site)
- [ ] Link to it from the Gumroad listing and from within the app

### 4.4 Trademark Compliance
- [x] Audit all instances of "GTD" in: *(done 2026-02-07, Round 2 completed 2026-02-07)*
  - [x] Application UI text *(10 instances found in Round 1, 10 replaced/cleaned)*
  - [x] Backend API descriptions, schema fields, module display names *(Round 2: 20+ instances cleaned)*
  - [ ] Marketing copy / Gumroad description
  - [x] Code comments *(Round 2: cleaned in schemas, API endpoints, types, hooks)*
- [x] Replace "GTD" in user-facing text with generic alternatives: *(done 2026-02-07)*
  - Round 1: "GTD + Momentum" → "Intelligent Momentum", "GTD: Define..." → "Define...", etc.
  - Round 2: "GTD Capture" → "Quick Capture", "GTD Inbox" → "Inbox", "GTD horizons" → "planning horizons"
  - Round 2: Schema descriptions cleaned ("GTD: What does..." → "What does...")
- [x] If referencing GTD methodology in docs/marketing, use proper attribution:
  - Added trademark notice in LICENSE file
  - OnboardingPage uses registered trademark symbol
  - AI prompt retains "Getting Things Done®" with proper attribution
- [x] Review "PARA" and "Second Brain" usage *(done 2026-02-07 Round 2)*:
  - "Second Brain Sync" → "File Sync" (Layout footer, Settings heading)
  - "Second Brain Root" → "Sync Folder Root" (Settings label)
  - "Second Brain integration" → "markdown file sync" (API description)
  - "Folder path in Second Brain" → "Folder path in synced notes" (schemas)
  - "PARA methodology recommends..." → "Best practice is to..." (Projects page)
  - "PARA structure" → "project-area structure" (Weekly Review page)
- [x] Choose a product name that avoids all trademarked terms: **Conduital** *(decided 2026-02-07)*

### 4.5 Add LICENSE File to Repository
- [x] Decide on the license for your product *(proprietary / commercial)*
- [x] Create a `LICENSE` file stating the software is proprietary *(done 2026-02-07)*
- [x] Replace the "Private project for personal use" marker with the proper license text
- [x] Ensure third-party license notices are bundled: *(done 2026-02-07)*
  - [x] Generate a list of all dependencies and their licenses *(all permissive: MIT, BSD, Apache 2.0, ISC)*
  - [x] Include a `THIRD_PARTY_LICENSES.txt` in the distribution *(35+ dependencies documented)*
  - [x] MIT/BSD/Apache licenses require attribution in the distributed product *(covered by THIRD_PARTY_LICENSES.txt)*

---

## Phase 5 — Gumroad Setup & Launch

### 5.1 Pre-Launch Assets
- [ ] Create application icon (multiple sizes: 16x16 through 256x256, `.ico` format)
- [ ] Take polished screenshots of the application (5–8 showing key features)
- [ ] Write a product description for Gumroad:
  - [ ] Headline and hook
  - [ ] Feature list (avoiding trademarked terms)
  - [ ] System requirements (Windows 10/11, disk space, internet for AI features)
  - [ ] What's included (installer, license key, access to updates)
  - [ ] FAQ: Do I need an Anthropic API key? (Answer: only for AI features, optional)
- [ ] Create a simple product landing page or website (optional but recommended)
- [ ] Record a demo video or GIF walkthrough (optional but highly effective for sales)

### 5.2 Pricing Strategy
- [ ] Research comparable tools and their pricing:
  - [ ] Todoist, Things 3, Amazing Marvin, Notion, Obsidian
  - [ ] Factor in the AI integration as a differentiator
- [ ] Decide on pricing model:
  - [ ] One-time purchase (simplest for MVP)
  - [ ] One-time with paid major version upgrades
  - [ ] Subscription (more complex, better recurring revenue)
- [ ] Set the launch price
- [ ] Consider a launch discount to drive initial sales and reviews

### 5.3 Gumroad Product Setup
- [ ] Create a Gumroad account (if not already)
- [ ] Set up the product listing:
  - [ ] Upload the signed installer as the deliverable file
  - [ ] Configure license key generation (enable Gumroad's license key feature)
  - [ ] Set price and currency
  - [ ] Add product description, screenshots, and cover image
  - [ ] Configure the "Thank You" / delivery page with:
    - Download link
    - License key display
    - Quick start instructions
    - Support contact info
- [ ] Test the full purchase flow:
  - [ ] Buy the product yourself (Gumroad allows test purchases)
  - [ ] Confirm the download works
  - [ ] Confirm the license key works in the app
  - [ ] Confirm the receipt email looks correct

### 5.4 Support Infrastructure
- [ ] Set up a dedicated support email address
- [ ] Create a basic FAQ / troubleshooting document covering:
  - [ ] Installation issues (SmartScreen warnings, antivirus false positives)
  - [ ] How to configure sync folder path
  - [ ] How to set up Anthropic API key
  - [ ] How to migrate data / back up database
  - [ ] Common error messages and solutions
- [ ] Decide where support docs live (website, GitHub wiki, Notion public page, etc.)

### 5.5 Update Mechanism (MVP)
- [ ] Implement a version check:
  - [ ] App checks a remote endpoint on startup (e.g., a JSON file hosted on GitHub Pages or your website)
  - [ ] Compares running version to latest available version
  - [ ] If update available: show a non-intrusive notification with a download link
- [ ] Establish a process for releasing updates:
  - [ ] Build new version with PyInstaller
  - [ ] Sign the new installer
  - [ ] Upload to Gumroad (update the product file)
  - [ ] Update the version check endpoint
  - [ ] Notify existing customers (Gumroad can send update emails)

---

## Future Roadmap Items (Post-MVP)

### Android Version
- [ ] Evaluate feasibility based on current tech stack (Python/React — likely requires a rebuild or API-hosted approach)
- [ ] Research cross-platform options: React Native (reuses React knowledge), Flutter, or hosted web app with mobile wrapper
- [ ] Decide: native mobile app vs. responsive web app accessible from mobile browser
- [ ] If pursuing: Google Play Store registration ($25 one-time), review guidelines

### Additional Distribution Channels
- [ ] Microsoft Store submission
- [ ] Direct sales from own website (with Stripe/Paddle instead of Gumroom)
- [ ] macOS / Linux versions (PyInstaller supports both; test and create platform-specific installers)

### Product Enhancements for Distribution
- [ ] Auto-updater (Squirrel.Windows or custom solution)
- [ ] Telemetry / crash reporting (opt-in, with clear disclosure)
- [ ] Offline license validation (for users with intermittent internet)
- [ ] Multi-device sync (would require a cloud component)
- [ ] Docker distribution for self-hosting / NAS users

### Marketing & Launch (Post-MVP)

#### Pre-Launch Assets
- [ ] Build waitlist / landing page on conduital.com
- [ ] Prepare press kit (screenshots, product description, founder bio)
- [ ] Draft ProductHunt and Show HN launch posts
- [ ] Create 5–8 polished app screenshots for Gumroad / marketing

#### Content & Community
- [ ] Start "building in public" content on X (@conduital)
- [ ] Write 2–3 foundational blog posts (philosophy: local-first, data ownership, AI as optional layer)
- [ ] Create launch blog post for conduital.com
- [ ] Set up email newsletter (ConvertKit / Buttondown) with waitlist integration
- [ ] Establish community channel (Discord or GitHub Discussions)

#### Launch Sequence
- [ ] Invite early adopter cohort (50–100 users) for beta feedback
- [ ] Collect testimonials and user workflow examples before public launch
- [ ] Execute staggered launch: ProductHunt → HN → Reddit (r/productivity, r/selfhosted, r/PKMS) → LinkedIn
- [ ] Run launch week engagement (respond to all comments, daily updates)

#### Ongoing Marketing
- [ ] Identify and pitch relevant podcasts (productivity, indie maker, local-first)
- [ ] Cross-post technical content to Dev.to / Hashnode
- [ ] Create YouTube tutorials (feature demos, workflow walkthroughs)
- [ ] Monitor brand mentions and category keywords across platforms

#### Content Pillars (for reference)
1. **Education** (40%) — Workflow guides, migration guides, productivity system comparisons
2. **Philosophy** (25%) — Local-first, data ownership, productivity without surveillance
3. **Technical** (20%) — Architecture decisions, AI integration patterns, sync design
4. **Community** (15%) — User workflows, success stories, weekly review rituals

#### Metrics to Track Post-Launch
- Social followers, blog traffic, newsletter subscribers
- Gumroad conversion rate, trial-to-purchase ratio
- Community size and engagement
- Content performance by platform and pillar

---

## Quick Reference: Tool & Account Checklist

| Item | Purpose | Cost | When Needed |
|------|---------|------|-------------|
| Code signing certificate | Sign installer to avoid SmartScreen warnings | $200–500/year | Phase 3 |
| Inno Setup | Create Windows installer | Free | Phase 3 |
| PyInstaller | Bundle Python app into standalone exe | Free | Phase 2 |
| Gumroad account | Sell and distribute the product | Free (they take a cut per sale) | Phase 5 |
| Clean Windows 10 VM | Test installation on fresh system | Free (Windows evaluation ISOs) | Phase 2–3 |
| Clean Windows 11 VM | Test installation on fresh system | Free (Windows evaluation ISOs) | Phase 2–3 |
| Domain name (optional) | Product website, update endpoint | ~$12/year | Phase 5 |
| Support email | Customer support | Free (or use existing) | Phase 5 |
