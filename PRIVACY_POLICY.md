# Conduital — Privacy Policy

**Effective Date:** February 25, 2026
**Last Updated:** February 25, 2026

---

## Summary

Conduital is a local-first productivity application. Your data stays on your computer. We do not collect, transmit, or store any of your personal data on our servers.

---

## 1. Data Storage

All data you create in Conduital — projects, tasks, areas, memory objects, session summaries, and settings — is stored locally on your computer in:

- **Database:** `%LOCALAPPDATA%\Conduital\tracker.db` (SQLite)
- **Configuration:** `%LOCALAPPDATA%\Conduital\config.env`
- **Logs:** `%LOCALAPPDATA%\Conduital\logs\`

We have no access to this data. You own it completely.

## 2. Data We Do NOT Collect

Conduital does **not**:

- Send telemetry or usage analytics
- Track your behavior or feature usage
- Phone home to any server
- Require an internet connection for core functionality
- Create user accounts on our systems
- Access your files outside the configured sync folder

## 3. Third-Party Services

Conduital integrates with two optional third-party services. These connections are initiated only by your explicit action:

### 3a. Anthropic API (AI Features — Optional)

If you provide your own Anthropic API key in Settings, Conduital sends requests to the Anthropic API to power AI features (suggestions, task decomposition, review summaries).

- **What is sent:** Task and project text you explicitly submit to AI features, plus system prompts
- **What is NOT sent:** Your full database, settings, or any data beyond the specific AI request
- **Your responsibility:** Usage of the Anthropic API is under your own API key and Anthropic's terms of service. Costs are between you and Anthropic.
- **Anthropic's privacy policy:** https://www.anthropic.com/privacy

You can use Conduital without an API key. All non-AI features work fully offline.

### 3b. Gumroad (License Validation — Future)

A future version may validate your license key via Gumroad's API. If implemented:

- **What is sent:** Your license key only
- **When:** On first activation and periodic re-validation
- **Gumroad's privacy policy:** https://gumroad.com/privacy

### 3c. File Sync (Optional)

If you configure a sync folder (e.g., a Google Drive or Dropbox folder), Conduital reads and writes markdown files to that folder. Conduital does not interact with cloud sync services directly — it only accesses local files. Any cloud synchronization is handled by your own sync client (Google Drive, Dropbox, etc.) under their respective terms.

## 4. Logs

Conduital writes application logs to `%LOCALAPPDATA%\Conduital\logs\`. These logs contain:

- Application startup/shutdown events
- Error messages and stack traces (for debugging)
- API request paths (no request bodies or personal data)

Logs remain on your computer. We never access or collect them.

## 5. Updates

Conduital may check for available updates by contacting a version-check endpoint. If implemented, this check transmits only the current application version number and receives the latest available version in response. No personal data, usage data, or identifiers are transmitted.

## 6. Children's Privacy

Conduital does not knowingly collect data from children under 13. Since no data is transmitted to us, this is not applicable in practice.

## 7. Changes to This Policy

We may update this privacy policy as Conduital evolves. Changes will be noted by updating the "Last Updated" date. Significant changes (e.g., introducing any data collection) will be communicated through the application's update notes.

## 8. Contact

If you have questions about this privacy policy:

- **Email:** support@conduital.com
- **Website:** https://conduital.com

---

*Conduital is built on the principle that your productivity data belongs to you.*
