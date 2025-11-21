# Render Deployment Troubleshooting Guide

## 502 Bad Gateway Error

If you're getting **502 Bad Gateway** errors, it means the application is crashing during startup. Here's how to diagnose and fix it:

### Step 1: Check Render Logs

1. Go to your Render dashboard
2. Click on your service
3. Go to the **"Logs"** tab
4. Look for error messages, especially:
   - `RuntimeError: DATABASE_URL environment variable is required`
   - Database connection errors
   - Import errors
   - Any Python tracebacks

### Step 2: Verify Environment Variables

In Render dashboard → Your Service → **Environment** tab, ensure you have:

**Required:**
- `DATABASE_URL` - Your PostgreSQL connection string (e.g., `postgresql://user:pass@host:5432/dbname`)
- `SECRET_KEY` - A random secret key for Flask sessions
- `WS_SECRET` - A secret key for WebSocket/SSE token signing (or it will use `SECRET_KEY`)

**Example DATABASE_URL format:**
```
postgresql://username:password@hostname:5432/database_name?sslmode=require
```

### Step 3: Common Issues

#### Issue 1: Missing DATABASE_URL
**Error:** `RuntimeError: DATABASE_URL environment variable is required`

**Fix:** 
1. Go to Render dashboard → Your Service → Environment
2. Add `DATABASE_URL` with your database connection string
3. Click "Save Changes"
4. Render will automatically redeploy

#### Issue 2: Database Connection Timeout
**Error:** Database connection errors in logs

**Fix:**
- Check if your database is accessible from Render's IPs
- For Supabase/Neon: Ensure connection string includes `?sslmode=require`
- Verify database credentials are correct
- Check if database has connection limits (free tiers often have limits)

#### Issue 3: Port Binding Issue
**Error:** "No open HTTP ports detected"

**Fix:**
- This is usually a false alarm if Gunicorn shows "Listening at: http://0.0.0.0:10000"
- Render uses port 10000 by default
- Check that your `Procfile` or Start Command is: `gunicorn --config gunicorn.conf.py wsgi:app`

#### Issue 4: Python Version Mismatch
**Error:** Import errors or compatibility issues

**Fix:**
- Ensure `runtime.txt` contains: `python-3.11.8`
- Or set Python version in Render dashboard → Environment → Python Version

### Step 4: Test Database Connection

You can test if your database is accessible by checking Render logs after deployment. The app will log:
- `Database initialized successfully` - ✅ Good
- `Error initializing database: ...` - ❌ Check connection string

### Step 5: Verify Service is Running

After fixing issues, check:
1. **Logs** should show: `Listening at: http://0.0.0.0:10000`
2. **Logs** should show: `Booting worker with pid: XX` (multiple workers)
3. **Health endpoint** should respond: `https://your-app.onrender.com/health`

### Quick Checklist

- [ ] `DATABASE_URL` is set in Render environment variables
- [ ] Database connection string is correct (test it locally if possible)
- [ ] `SECRET_KEY` is set
- [ ] `runtime.txt` specifies Python 3.11.8
- [ ] `Procfile` or Start Command uses `wsgi:app`
- [ ] No syntax errors in code (check logs)
- [ ] Database is accessible (not blocked by firewall)

### Still Having Issues?

1. **Check full logs** - Look for the first error message
2. **Test locally** - Run `python wsgi.py` locally with the same `DATABASE_URL`
3. **Simplify** - Temporarily comment out database initialization to see if app starts
4. **Contact Support** - Render support can help with infrastructure issues

## Testing After Fix

Run the test script:
```bash
python test_render_deployment.py
```

Or manually test:
```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{"status": "ok", "service": "code-broadcasting-system"}
```

