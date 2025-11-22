# Local Testing Setup Guide

## Setting Up Production Database Connection

The test scripts (`test_sse_helper.py`) now use the **production database** instead of a local database.

### Quick Setup

**Windows PowerShell:**
```powershell
# Set for current session
$env:DATABASE_URL="postgresql://postgres.oahhrydngdyilxjdwhqt:XUJ-XUJ-XUJ@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

# Or run the setup script
.\setup_env.ps1
```

**Linux/Mac:**
```bash
# Set for current session
export DATABASE_URL="postgresql://postgres.oahhrydngdyilxjdwhqt:XUJ-XUJ-XUJ@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

# Or run the setup script
source setup_env.sh
```

**Permanent Setup (Recommended):**

Create a `.env` file in the project root:
```
DATABASE_URL=postgresql://postgres.oahhrydngdyilxjdwhqt:XUJ-XUJ-XUJ@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
```

The script will automatically load this via `python-dotenv`.

### Verify Setup

```bash
# Check if DATABASE_URL is loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('DATABASE_URL:', 'SET' if os.getenv('DATABASE_URL') else 'NOT SET')"

# Test database connection
python test_sse_helper.py verify bharat
```

### Important Notes

1. **All test scripts use production database** - The `create_user()` function connects directly to the production database using `DATABASE_URL`.

2. **HTTP API vs Database** - The `verify_user()` function checks both:
   - Direct database connection (uses `DATABASE_URL`)
   - HTTP API endpoint (tests the production server at `https://system-main-v2.onrender.com`)

3. **Production Server** - Make sure your Render deployment also has `DATABASE_URL` set to the same value in the environment variables.

### Testing Commands

```bash
# Create user in production database
python test_sse_helper.py create bharat

# Verify user (checks both DB and HTTP API)
python test_sse_helper.py verify bharat

# Send test code
python test_sse_helper.py send bharat TEST-123

# Run all tests
python test_sse_helper.py test-all bharat
```

### Troubleshooting

**"DATABASE_URL not set" error:**
- Make sure you've set the environment variable or created a `.env` file
- Restart your terminal/PowerShell after setting environment variables
- Check with: `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DATABASE_URL'))"`

**Connection errors:**
- Verify the database URL is correct
- Check if the database is accessible from your network
- Ensure SSL/TLS settings are correct if required

