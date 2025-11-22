# Render Deployment Checklist

## ✅ Pre-Deployment Verification

### 1. Database Configuration
- [x] **Codebase uses production database only** - `app/database.py` requires `DATABASE_URL`
- [x] **No local database fallbacks** - Application will fail to start if `DATABASE_URL` is not set
- [x] **All database operations use production DB** - All services use `db_session()` from `app/database.py`

### 2. Environment Variables Required on Render

Set these in **Render Dashboard → Your Service → Environment**:

```
DATABASE_URL=postgresql://postgres.oahhrydngdyilxjdwhqt:XUJ-XUJ-XUJ@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
```

**Optional but recommended:**
```
WS_SECRET=your-secret-key-here
SECRET_KEY=your-secret-key-here
SOCKETIO_ASYNC_MODE=eventlet
```

### 3. Files Ready for Deployment
- [x] `system.db` removed (no local database files)
- [x] `.gitignore` created (prevents committing sensitive files)
- [x] `requirements.txt` up to date
- [x] `runtime.txt` specifies Python version (3.11.8)
- [x] `Procfile` configured for Gunicorn
- [x] `gunicorn.conf.py` configured
- [x] `wsgi.py` entry point ready

### 4. Code Verification

**Database Connection:**
- ✅ `app/database.py` - Requires `DATABASE_URL`, no SQLite fallback
- ✅ `app/__init__.py` - Uses `init_db()` which connects to production DB
- ✅ `app/services/user_service.py` - Uses `SessionLocal` from production DB
- ✅ All routes use `db_session()` context manager

**No Local Database References:**
- ✅ No `system.db` file
- ✅ No SQLite fallbacks in active code
- ✅ `old_app.py` is legacy (not used)

## 🚀 Deployment Steps

### Step 1: Set Environment Variables on Render

1. Go to **Render Dashboard** → Your Service
2. Click **Environment** tab
3. Add/Update these variables:

```
DATABASE_URL=postgresql://postgres.oahhrydngdyilxjdwhqt:XUJ-XUJ-XUJ@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
```

### Step 2: Verify Start Command

In Render Dashboard → Your Service → Settings:
- **Start Command:** `gunicorn --config gunicorn.conf.py wsgi:app`

### Step 3: Push Code

```bash
git add .
git commit -m "Configure for production database only"
git push origin master
```

### Step 4: Monitor Deployment

1. Watch the **Logs** tab in Render
2. Look for: `Database initialized successfully`
3. Verify health check: `https://system-main-v2.onrender.com/health`

## 🔍 Post-Deployment Verification

### Test Endpoints:

```bash
# Health check
curl https://system-main-v2.onrender.com/health

# Verify user (should work if user exists in production DB)
curl https://system-main-v2.onrender.com/api/users/bharat/verify

# Send test code
curl -X POST https://system-main-v2.onrender.com/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"username":"bharat","code":"TEST-123","source":"deployment-test"}'
```

### Expected Logs:

```
[INFO] Initializing database...
[INFO] Database initialized successfully
[INFO] Starting user service...
[INFO] User service started successfully
[INFO] Gunicorn server is ready to accept connections
```

## ⚠️ Troubleshooting

**If you see "DATABASE_URL environment variable is required":**
- Check Render Dashboard → Environment → DATABASE_URL is set
- Verify the connection string is correct
- Redeploy after setting the variable

**If database connection fails:**
- Verify DATABASE_URL is correct
- Check if database allows connections from Render's IP
- Verify SSL/TLS settings if required

**If app starts but can't find users:**
- Verify users exist in the production database
- Check database connection is working: `curl https://system-main-v2.onrender.com/health`
- Review logs for database errors

## 📝 Notes

- **All code uses production database** - No local database fallbacks
- **DATABASE_URL is required** - Application will not start without it
- **Same database for local and production** - Use the same DATABASE_URL for local testing
- **Test scripts use production DB** - `test_sse_helper.py` uses DATABASE_URL from environment

