#!/bin/bash
# Bash script to set DATABASE_URL for local testing
# Run this before using test scripts: source setup_env.sh

export DATABASE_URL="postgresql://postgres.oahhrydngdyilxjdwhqt:XUJ-XUJ-XUJ@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

echo "✅ DATABASE_URL is now set!"
echo "To make it permanent, add it to your ~/.bashrc or ~/.zshrc:"
echo "  export DATABASE_URL='postgresql://postgres.oahhrydngdyilxjdwhqt:XUJ-XUJ-XUJ@aws-1-ap-south-1.pooler.supabase.com:6543/postgres'"
echo ""
echo "To test, run: python test_sse_helper.py verify bharat"

