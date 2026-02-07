# Troubleshooting Guide - Project Tracker

## Issue: "Failed to load project" when clicking View Details

### Problem Description
When clicking "View Details" on a project card, the ProjectDetail page shows an error: "Failed to load project"

### Common Causes & Solutions

#### 1. Backend Server Not Running

**Check if backend is running:**
```bash
# Navigate to backend directory
cd C:\Dev\project-tracker\backend

# Check if server is running on port 8000
# Open browser and visit: http://localhost:8000/docs
```

**Solution:**
```bash
# Start the backend server
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend should show:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

#### 2. Database Not Initialized

**Check if database exists:**
```bash
ls backend/project_tracker.db
```

**Solution - Initialize database:**
```bash
cd backend
# Run database migrations or initialization script
python -m app.database.init_db
```

#### 3. CORS Configuration Issue

**Symptoms:**
- Browser console shows CORS errors
- Network tab shows failed preflight requests

**Solution:**
Check `backend/app/main.py` has CORS middleware:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 4. API Endpoint Issues

**Debug Steps:**

1. **Check browser console** (F12 -> Console tab):
   - Look for error messages
   - Note the HTTP status code (404, 500, etc.)

2. **Check Network tab** (F12 -> Network tab):
   - Find the failed request to `/api/v1/projects/{id}`
   - Click on it to see:
     - Request URL
     - Response status
     - Response body
     - Request headers

3. **Test API directly:**
   ```bash
   # Replace {id} with actual project ID
   curl http://localhost:8000/api/v1/projects/1
   ```

#### 5. Invalid Project ID

**Symptoms:**
- Console shows "ProjectDetail - Parsed ID: NaN"
- URL shows malformed ID

**Check:**
1. Open browser console (F12)
2. Look for logs: `ProjectDetail - ID from URL: ...`
3. Verify the ID is a valid number

**Solution:**
- Ensure project IDs in database are valid integers
- Check ProjectCard component is passing correct ID in Link

#### 6. Missing Project Data

**Symptoms:**
- Request succeeds (200 OK)
- But `project` is null or undefined

**Solution:**
```bash
# Check if project exists in database
cd backend
python
>>> from app.core.database import SessionLocal
>>> from app.models.project import Project
>>> db = SessionLocal()
>>> projects = db.query(Project).all()
>>> print([(p.id, p.title) for p in projects])
```

### Debugging Steps

#### Step 1: Enable Detailed Error Logging

The ProjectDetail page now logs detailed error information. Check browser console:

```javascript
// Should see:
ProjectDetail - ID from URL: 1 Parsed ID: 1
ProjectDetail - Loading: true Error: undefined Project: undefined
// ... then after loading ...
ProjectDetail - Loading: false Error: [error details] Project: undefined
```

#### Step 2: Verify API Call

Open Network tab and verify:
- **Request URL:** `http://localhost:5173/api/v1/projects/1`
- **Proxied to:** `http://localhost:8000/api/v1/projects/1`
- **Status:** Should be 200
- **Response:** Should contain project JSON

#### Step 3: Check Backend Logs

Look at backend terminal for errors:
```
INFO:     127.0.0.1:xxxxx - "GET /api/v1/projects/1 HTTP/1.1" 200 OK
```

If you see 404 or 500, check backend code.

#### Step 4: Verify Database Connection

```bash
cd backend
python -c "from app.core.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

Should show: `['projects', 'tasks', 'areas', ...]`

### Quick Fix Checklist

- [ ] Backend server is running on port 8000
- [ ] Frontend dev server is running on port 5173
- [ ] Can access http://localhost:8000/docs
- [ ] Database file exists and has data
- [ ] Browser console shows detailed error logs
- [ ] Network tab shows the API request
- [ ] No CORS errors in console
- [ ] Project ID in URL is valid number

### Manual Testing

1. **Test backend directly:**
   ```bash
   curl http://localhost:8000/api/v1/projects
   ```
   Should return list of projects.

2. **Test specific project:**
   ```bash
   curl http://localhost:8000/api/v1/projects/1
   ```
   Should return single project with tasks.

3. **Create test project:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/projects \
     -H "Content-Type: application/json" \
     -d '{"title": "Test Project", "status": "active", "priority": 5}'
   ```

### Environment Verification

**Frontend (.env or vite.config.ts):**
```typescript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

**Backend (.env):**
```env
DATABASE_URL=sqlite:///./project_tracker.db
API_V1_PREFIX=/api/v1
```

### Common Error Messages & Solutions

#### "Failed to load project: Network Error"
- **Cause:** Backend not running or not accessible
- **Solution:** Start backend server

#### "Failed to load project: Request failed with status code 404"
- **Cause:** Project doesn't exist or wrong ID
- **Solution:** Check project ID and database

#### "Failed to load project: Request failed with status code 500"
- **Cause:** Backend error (database, code bug)
- **Solution:** Check backend logs for stack trace

#### "Failed to load project: undefined"
- **Cause:** Unknown error, possibly network
- **Solution:** Check all connections, restart servers

### Getting More Help

1. **Share console output:**
   - Open browser console (F12)
   - Copy all red errors
   - Share in issue report

2. **Share network details:**
   - Open Network tab
   - Find failed request
   - Right-click -> "Copy as cURL"
   - Share the command

3. **Share backend logs:**
   - Copy last 20 lines from backend terminal
   - Share in issue report

### Prevention

To avoid this issue:

1. **Always start backend first:**
   ```bash
   cd backend && python -m uvicorn app.main:app --reload
   ```

2. **Then start frontend:**
   ```bash
   cd frontend && npm run dev
   ```

3. **Use a process manager** like PM2 or docker-compose to manage both:
   ```yaml
   # docker-compose.yml
   services:
     backend:
       build: ./backend
       ports:
         - "8000:8000"
     frontend:
       build: ./frontend
       ports:
         - "5173:5173"
       depends_on:
         - backend
   ```

---

## Additional Issues

### Forms Not Submitting

If create/edit forms are not working:

1. Check browser console for errors
2. Verify backend endpoints exist:
   - POST /api/v1/projects
   - PUT /api/v1/projects/{id}
   - POST /api/v1/tasks
   - PUT /api/v1/tasks/{id}
3. Check network tab for failed requests
4. Verify React Query devtools for mutation state

### Modal Not Closing After Submit

If modals stay open after successful submission:

1. Check if `onSuccess` callback is firing
2. Verify `queryClient.invalidateQueries` is working
3. Check for console errors
4. Ensure mutation is actually succeeding (check network tab)

---

*Last updated: January 22, 2026*
