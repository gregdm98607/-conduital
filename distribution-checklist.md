# Conduital — Windows MVP Distribution Checklist

**Goal:** Package Conduital as a Windows desktop product and sell via Gumroad.
**Target Timeline:** 4–6 weeks (part-time)
**Last Updated:** February 7, 2026

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
  - conduital.com AVAILABLE ($4.99), conduital.io AVAILABLE, conduital.app AVAILABLE ($19.99)
  - USPTO: ZERO results (no live or dead filings)
  - GitHub @conduital: AVAILABLE
  - Twitter/X @conduital: AVAILABLE
  - Gumroad: AVAILABLE
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
- [ ] Test the full app running with only the Python backend (no `npm run dev`)
- [ ] Verify all frontend routes, API calls, and assets load correctly from the static build
- [x] Update `vite.config.ts` if needed to set correct `base` path for production *(N/A — default "/" is correct)*

### 1.2 Auto-Run Database Migrations on Startup
- [x] Wire Alembic `upgrade head` into the FastAPI startup lifecycle event *(done 2026-02-07 — `run_migrations()` in lifespan)*
- [x] Handle the case where the database file doesn't exist yet (first run) — create the directory and file *(done — `db_dir.mkdir(parents=True, exist_ok=True)` in lifespan)*
- [x] Handle the case where migrations are already current (no-op, no errors) *(Alembic handles this natively)*
- [ ] Test upgrading from an empty state to fully migrated
- [ ] Test upgrading from a mid-point (simulating an app update with new migrations)
- [x] Add error handling and logging for migration failures *(done — try/except with fallback to create_all)*

### 1.3 Define User Data Directory
- [ ] Choose a standard Windows location for app data (e.g., `%LOCALAPPDATA%\ProjectTracker\`)
- [ ] Store the following in this directory:
  - [ ] SQLite database file (`tracker.db`)
  - [ ] Generated JWT secret
  - [ ] User configuration / settings file (replaces `.env` for end users)
  - [ ] Log files
- [ ] Create the directory automatically on first run if it doesn't exist
- [ ] Ensure all file paths in the app reference this directory dynamically (no hardcoding)

### 1.4 Build First-Run Setup Wizard
- [ ] Design a setup flow as a page/modal in the React frontend
- [ ] Step 1: Welcome screen explaining what the app does
- [ ] Step 2: Second Brain folder selection
  - [ ] Implement a folder picker (either native dialog via API endpoint or manual path entry)
  - [ ] Validate the selected path exists and is accessible
  - [ ] Explain what the app will do with this folder
  - [ ] Allow skipping (sync features disabled)
- [ ] Step 3: Anthropic API key (optional)
  - [ ] Text input with paste support
  - [ ] "Test Connection" button that validates the key via API call
  - [ ] Clear messaging: "AI features are optional. Without a key, all other features work normally."
  - [ ] Link to Anthropic's signup page for users who don't have a key
  - [ ] Explain that usage costs are between the user and Anthropic
- [ ] Step 4: Confirmation / "Get Started" screen
- [ ] Save all configuration to the user data directory
- [ ] Add a flag/marker so the wizard only shows on first run
- [ ] Provide a way to re-run setup or edit settings later from within the app

### 1.5 Verify Graceful AI Degradation
- [ ] Launch the app with no Anthropic API key configured
- [ ] Test every AI-powered feature and confirm:
  - [ ] No unhandled exceptions or crashes
  - [ ] UI elements for AI features show a clear "requires API key" or "set up in settings" state
  - [ ] Non-AI features all function normally
- [ ] Test with an invalid API key — confirm helpful error message, not a stack trace
- [ ] Test with a valid key that has exceeded its quota — confirm graceful handling

### 1.6 Single-Process Launch Architecture
- [x] Create a Python entry point script *(done 2026-02-07 — `backend/run.py`)*
  - [ ] Checks if first run → triggers setup wizard *(deferred to 1.4)*
  - [x] Runs Alembic migrations *(handled by lifespan in main.py)*
  - [x] Starts Uvicorn serving the FastAPI app (which includes static frontend)
  - [x] Opens the user's default browser to `http://localhost:<PORT>`
  - [x] Handles clean shutdown *(KeyboardInterrupt + signal handling)*
- [x] Choose a default port *(52140 — unlikely to conflict)*
- [x] Implement port conflict detection: check if port is in use, increment if necessary *(find_available_port())*
- [x] Store the active port so the browser opens to the correct URL

---

## Phase 2 — PyInstaller Packaging

### 2.1 Initial PyInstaller Setup
- [ ] Install PyInstaller in the project (`pip install pyinstaller`)
- [ ] Create an initial `.spec` file by running `pyinstaller --name ProjectTracker run.py`
- [ ] Configure the `.spec` file:
  - [ ] Add `frontend/dist/` as a data directory (the built static files)
  - [ ] Add Alembic migration files as data
  - [ ] Add `alembic.ini` as data
  - [ ] Add any other non-Python assets (templates, default configs)
  - [ ] Set the application icon (`.ico` file)

### 2.2 Resolve Packaging Issues
- [ ] Run the first build and catalog all errors
- [ ] Handle hidden imports — FastAPI, SQLAlchemy, and Pydantic often need explicit imports listed:
  - [ ] `uvicorn.logging`
  - [ ] `uvicorn.loops.auto`
  - [ ] `uvicorn.protocols.http.auto`
  - [ ] SQLAlchemy dialect imports
  - [ ] Pydantic internal modules
  - [ ] Any other modules PyInstaller fails to detect
- [ ] Handle native extensions:
  - [ ] `python-jose[cryptography]` — ensure cryptography wheels are bundled
  - [ ] `watchdog` — test file watching works in packaged form
  - [ ] `uvicorn[standard]` — confirm fallback to pure-Python if C extensions fail
- [ ] Verify the bundled SQLite works correctly (WAL mode)

### 2.3 System Tray Integration
- [ ] Add `pystray` (or similar) as a dependency
- [ ] Create a system tray icon with menu:
  - [ ] "Open Project Tracker" — opens/focuses the browser tab
  - [ ] "Settings" — opens settings page in browser
  - [ ] Separator
  - [ ] "About" — shows version info
  - [ ] "Quit" — cleanly shuts down the server and exits
- [ ] Design or source an application icon (`.ico` format for Windows)
- [ ] Ensure the app runs as a tray application (no visible console window)
- [ ] Handle the case where the user closes the browser tab — tray icon persists, re-openable

### 2.4 Build & Test Cycle
- [ ] Build the full package with PyInstaller
- [ ] Test on your development machine — confirm everything works
- [ ] **Test on a clean Windows 10 VM** (no Python, no Node.js installed):
  - [ ] Does the app launch?
  - [ ] Does the browser open correctly?
  - [ ] Does first-run setup work?
  - [ ] Do all features function (minus AI if no key)?
  - [ ] Does the system tray icon appear and work?
  - [ ] Does the app shut down cleanly?
- [ ] **Test on a clean Windows 11 VM** — repeat all above
- [ ] Note and fix any missing DLLs, import errors, or path issues
- [ ] Check the final package size — aim for reasonable (under 100–150 MB ideally)
- [ ] Test startup time — should feel responsive (under 5–10 seconds to browser open)

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
- [ ] Verify the signature (`signtool verify /pa ProjectTracker.exe`)

### 3.2 Create Installer with Inno Setup
- [ ] Download and install Inno Setup
- [ ] Create the installer script (`.iss` file) covering:
  - [ ] App name, version, publisher info
  - [ ] Installation directory (default: `C:\Program Files\ProjectTracker\`)
  - [ ] All files from the PyInstaller output
  - [ ] Start Menu shortcut creation
  - [ ] Optional Desktop shortcut
  - [ ] Uninstaller registration in Windows "Apps & Features"
  - [ ] Application icon
  - [ ] License agreement screen (display EULA during install)
  - [ ] Optional: "Launch Project Tracker" checkbox on final screen
- [ ] Build the installer
- [ ] Sign the installer `.exe` with the code signing certificate
- [ ] Test the full install → launch → use → uninstall cycle on clean VMs:
  - [ ] Windows 10 VM
  - [ ] Windows 11 VM
- [ ] Verify uninstaller removes all files from Program Files
- [ ] Decide: should uninstall remove user data (`%LOCALAPPDATA%\ProjectTracker\`) or leave it? (Standard practice: leave it, with optional "remove all data" checkbox)

### 3.3 Version Management
- [x] Establish a versioning scheme *(SemVer per STRAT-008: Major.Minor.Patch)*
- [x] Set version number in: *(set to 1.0.0-alpha on 2026-02-07)*
  - [x] Python package config (`backend/pyproject.toml`)
  - [x] Frontend `package.json`
  - [x] Backend config (`backend/app/core/config.py`)
  - [x] `.env.example`
  - [ ] PyInstaller `.spec` file *(not yet created)*
  - [ ] Inno Setup `.iss` file *(not yet created)*
- [ ] Consider a single source of truth for version number (one file read by all)

---

## Phase 4 — Licensing, Legal & Compliance

### 4.1 License Key System (Gumroad Integration)
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

### 4.2 EULA (End User License Agreement)
- [ ] Draft or have drafted a EULA covering:
  - [ ] License grant (what the user is allowed to do)
  - [ ] Number of devices / installations allowed
  - [ ] Restrictions (no reverse engineering, redistribution, etc.)
  - [ ] AI features disclaimer: user provides their own Anthropic API key; usage costs are theirs; Anthropic's terms apply
  - [ ] Data handling: all data stored locally on user's machine; app does not transmit user data to the developer
  - [ ] No warranty / limitation of liability
  - [ ] Termination conditions
- [ ] Have the EULA reviewed (ideally by a lawyer, at minimum by an AI legal review)
- [ ] Embed EULA in the installer (displayed during installation)
- [ ] Make EULA accessible within the app (About/Legal section)

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
  - [ ] How to configure Second Brain path
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
