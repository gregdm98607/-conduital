# Quick Fix for Blank Page

## Most Likely Issue

The page is blank because of one of these issues:

1. Path alias (`@/`) not working in imports
2. Missing Node types for vite.config
3. Component import error
4. API client failing silently

## Fix 1: Add Missing Types (RECOMMENDED TRY FIRST)

```bash
cd C:\Dev\project-tracker\frontend
npm install --save-dev @types/node
```

Then restart the dev server:
```bash
npm run dev
```

## Fix 2: Use Simplified App (If Fix 1 Doesn't Work)

Replace `src/App.tsx` with this minimal version to test:

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div style={{ padding: '2rem' }}>
        <h1>Project Tracker</h1>
        <p>If you see this, React is working!</p>
      </div>
    </QueryClientProvider>
  );
}

export default App;
```

Reload http://localhost:5173

**If this works:** The issue is in the routes or page components.

**If this doesn't work:** Check browser console (F12) for errors.

## Fix 3: Check Console First!

Before trying anything else:

1. Open browser to http://localhost:5173
2. Press F12 (opens Developer Tools)
3. Click "Console" tab
4. Look for red error messages
5. **Take a screenshot or copy the error**

The error message will tell us exactly what's wrong!

## Fix 4: Verify All Dependencies

```bash
cd C:\Dev\project-tracker\frontend

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## Fix 5: Use Alternative Vite Config

Replace `vite.config.ts` with this version without path alias:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

If using this, you'll need to update imports in all files to use relative paths instead of `@/`.

## What To Do Next

**STEP 1:** Open browser console (F12) and share the errors you see
**STEP 2:** Try Fix 1 (install @types/node)
**STEP 3:** If still broken, try Fix 2 (simplified App)
**STEP 4:** Share the console errors with me

The console errors will tell us exactly what's failing!

## Expected Console Output (When Working)

When the app works correctly, you might see:
```
[vite] connected.
```

And NO red errors.

## Common Errors & What They Mean

**Error:** `Cannot find module '@/services/api'`
→ Path alias not working, need to fix vite.config.ts

**Error:** `Failed to fetch dynamically imported module`
→ Vite build issue, try restarting dev server

**Error:** `useQuery is not a function`
→ React Query import issue

**Error:** `Cannot read property 'createElement' of undefined`
→ React import issue

**Error:** Network request failed to localhost:8000
→ Backend not running (but page should still load)

Share the actual error and I'll provide the exact fix!
