# Debugging Steps - Blank Page Issue

## The Problem
- Frontend loads at http://localhost:5173
- Page is blank (no content renders)
- Browser console likely has errors

## Step 1: Check Browser Console

**CRITICAL:** Open your browser's Developer Tools and check the Console tab.

**How to open:**
- Chrome/Edge: Press `F12` or `Ctrl+Shift+J`
- Firefox: Press `F12` or `Ctrl+Shift+K`

Look for red error messages. Common issues:
- Import errors (module not found)
- Syntax errors in JSX
- Missing dependencies
- TypeScript type errors

**Please check the console and share what errors you see.**

## Step 2: Check Network Tab

While in Developer Tools, go to the Network tab:
- Is `/src/main.tsx` loading?
- Are there any 404 errors for files?
- Is the API accessible (if it's trying to call it)?

## Step 3: Verify Dependencies Are Installed

```bash
cd C:\Dev\project-tracker\frontend
npm install
```

Make sure this completes without errors.

## Step 4: Check Vite Dev Server Output

When you run `npm run dev`, the terminal should show:

```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h + enter to show help
```

Are there any error messages in the terminal?

## Step 5: Test with Minimal App

Let's create a simple test to isolate the issue:

```bash
cd C:\Dev\project-tracker\frontend\src
```

Backup your App.tsx:
```bash
cp App.tsx App.tsx.backup
```

Create a minimal test App.tsx:
```typescript
function App() {
  return <div className="p-8"><h1>Hello World</h1></div>;
}

export default App;
```

Then reload http://localhost:5173

**Does "Hello World" appear?**
- If YES: The issue is in one of the components/pages
- If NO: The issue is with React/Vite setup

## Common Issues & Solutions

### Issue 1: Module Import Errors

**Error:** `Cannot find module '@/...'`

**Solution:**
The path alias might not be working. Check `vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

### Issue 2: React Router Error

**Error:** Related to `BrowserRouter` or routing

**Solution:**
The router might be failing. Try the minimal App test above first.

### Issue 3: React Query Error

**Error:** Related to `QueryClient` or `useQuery`

**Solution:**
The API might be unreachable. But this should show loading state, not blank page.

### Issue 4: TypeScript Compilation Error

**Error:** Type errors in terminal

**Solution:**
Run `npm run build` to see TypeScript errors:
```bash
npm run build
```

Look for type errors and share them.

## Quick Fix: Simplify App.tsx

Replace the current App.tsx with this minimal version that doesn't use routing or API:

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Project Tracker
          </h1>
          <p className="text-gray-600">
            The app is loading correctly! Now let's add the router back...
          </p>
        </div>
      </div>
    </QueryClientProvider>
  );
}

export default App;
```

**Does this work?**
- If YES: The issue is with the routing or one of the page components
- If NO: There's a deeper issue with the setup

## What I Need From You

Please provide:

1. **Browser Console Errors** (screenshot or copy/paste)
2. **Terminal Output** from `npm run dev` (any errors?)
3. **Result of minimal App test** (does Hello World show?)
4. **Network Tab** - any failed requests?

Once I see the actual errors, I can provide a precise fix.

## Most Likely Issues

Based on the symptoms, the most likely causes are:

1. **Missing dependency** - Run `npm install` again
2. **Path alias not working** - Import errors for `@/...`
3. **Component error** - One of the pages has a syntax error
4. **React Router issue** - Router setup failing silently

Let me know what you find in the console!
