# ☁️ Deploy to Streamlit Cloud

Get your dashboard live in the cloud (completely free!)

---

## ✅ Prerequisites

- ✓ GitHub account (free: github.com)
- ✓ Streamlit Cloud account (free: share.streamlit.io)
- ✓ Working local version (follow [SIMPLE_START.md](SIMPLE_START.md))

---

## 🚀 5-Step Deployment

### Step 1: Push to GitHub

```bash
cd ~/Statistical  # or C:\Users\Asus\Statistical on Windows

# Add all changes
git add .

# Commit
git commit -m "Simplify: hardcoded config, no Docker, Streamlit Cloud ready"

# Push to GitHub
git push origin main
```

---

### Step 2: Go to Streamlit Cloud

Visit: https://share.streamlit.io/

Click blue **"New app"** button

---

### Step 3: Connect GitHub Repo

1. **Select Repository**
   - Choose your GitHub account
   - Select `Statistical` repository
   - Select `main` branch

2. **Set Main File**
   - Path: `streamlit_app/app.py`
   - Click **Deploy**

**That's it!** Streamlit handles everything else.

---

### Step 4: Wait for Deployment

You'll see a progress bar:
- Installing dependencies (1 min)
- Running app (30 sec)
- Live! (30 sec)

Total: ~2 minutes

---

### Step 5: Access Your Dashboard

Your app URL:
```
https://share.streamlit.io/yourusername/Statistical/main/streamlit_app/app.py
```

**Share with anyone!** They can use it immediately. 🎉

---

## 🔄 Auto-Updates

Every day at **6 PM IST**, GitHub Actions automatically:
- Downloads fresh stock data
- Updates signals
- Pushes results to GitHub
- **Your dashboard refreshes automatically!**

No manual work needed. Just runs in the background.

---

## 📊 Monitor Your Deployment

### In Streamlit Cloud:
1. Go to https://share.streamlit.io
2. Click your app
3. See "App health" and "Recent runs"
4. View logs if needed

### In GitHub:
1. Go to your repo
2. Click "Actions" tab
3. See `daily_update.yml` runs
4. Check if data/signals updated

---

## 🛠️ Troubleshooting

### "App not loading"
- Wait 2-3 minutes for first deployment
- Check app status in Streamlit Cloud dashboard
- Check GitHub Actions logs

### "Requirements error"
- Ensure `requirements.txt` is properly formatted
- Check for typos in package names
- Try locally first: `pip install -r requirements.txt`

### "Database not found"
- Database is created automatically on first run
- It persists across app restarts
- Data files stored in Streamlit Cloud's file system

### "Daily updates not running"
- Check GitHub repo's Actions tab
- Ensure `.github/workflows/daily_update.yml` exists
- Verify file is in `main` branch

---

## 📈 Performance Tips

### Streamlit Cloud Limitations
- **Memory**: 1 GB available
- **CPU**: 1 vCPU
- **Storage**: Limited temporary space
- **Runtime**: 1 hour max for scripts

Our app uses minimal resources, so no issues!

### Optimize if Needed
- Limit correlation window (adjust in `config.py`)
- Cache data locally instead of recalculating
- Use `@st.cache_data` decorators (already done)

---

## 🚨 Important Notes

### Cost
- **Free tier**: Unlimited apps
- **Pro tier**: $5-20/month (optional, not needed)
- Our app fits comfortably in free tier

### Data Privacy
- Your code is public on GitHub
- Stock data is public (Yahoo Finance)
- No secrets stored in code (hardcoded generic values)
- No API keys or credentials needed

### Uptime
- Streamlit Cloud apps sleep after 7 days of no views
- Access triggers wake-up automatically
- Still free!

---

## 🎯 What Happens After Deploy

1. **Streamlit Cloud runs your app:**
   - Installs `requirements.txt` packages
   - Executes `streamlit_app/app.py`
   - Serves on the web

2. **GitHub Actions runs daily (6 PM IST):**
   - Runs `src/pipeline.py`
   - Downloads new stock data
   - Generates new signals
   - Pushes updates to GitHub

3. **Your dashboard updates automatically:**
   - Fresh data every day
   - New signals available
   - Backtests recalculated
   - Zero manual work!

---

## 📱 Share Your Dashboard

Once live, share the URL:
```
https://share.streamlit.io/yourusername/Statistical/main/streamlit_app/app.py
```

**Friends can:**
- View your signals
- Run backtests
- Explore pairs
- Download analytics

**They cannot:**
- Modify code
- Change data
- Affect your app

---

## 🆘 Get Help

**Streamlit Issues:**
- Docs: docs.streamlit.io
- Community: discuss.streamlit.io

**GitHub Actions Issues:**
- Docs: github.com/features/actions
- Check workflow file: `.github/workflows/daily_update.yml`

**Our Project Issues:**
- Check logs locally first
- Ensure setup.bat/setup.sh completed
- Verify requirements.txt installed

---

## ✨ Next Steps

After deployment:

1. **Test the live app** - Confirm all pages work
2. **Share with friends** - Get feedback
3. **Monitor updates** - Check GitHub Actions logs
4. **Customize thresholds** - Edit `config.py` → commit → auto-redeploy
5. **Analyze performance** - Use backtest page

---

**Your dashboard is live! 🚀**

  --region us-central1 \
  --memory 2Gi \
  --port 8501
```

### Using EC2
```bash
# SSH to EC2 instance
ssh -i key.pem ec2-user@your-instance

# Clone repo and setup
git clone https://github.com/yourusername/statarb-platform.git
cd statarb-platform

# Install Python 3.9
sudo amazon-linux-extras install python3.9 -y

# Setup and run
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run Streamlit
streamlit run streamlit_app/app.py
```

## Option 4: Heroku Deployment

### Setup
```bash
# Create Procfile
cat > Procfile << EOF
web: streamlit run streamlit_app/app.py --server.port=\$PORT --server.address=0.0.0.0
EOF

# Create app.json
cat > app.json << EOF
{
  "name": "Statistical Arbitrage Platform",
  "description": "Pair trading signals for Indian equities",
  "repository": "https://github.com/yourusername/statarb-platform",
  "buildpacks": [
    {
      "url": "heroku/python"
    }
  ]
}
EOF
```

### Deploy
```bash
heroku login
heroku create your-app-name
git push heroku main

# View logs
heroku logs --tail
```

## GitHub Actions Configuration

### Daily Pipeline Setup

1. Create GitHub secret `SLACK_WEBHOOK_URL` (optional for notifications)
2. Workflows run automatically on schedule
3. Check `.github/workflows/daily_update.yml`

### Manual Trigger
```bash
gh workflow run daily_update.yml --ref main
```

## Database Persistence

### SQLite (Development)
- File location: `data/statarb.db`
- Synced to GitHub via daily action
- Portable but limited concurrency

### PostgreSQL (Production)

Update `requirements.txt`:
```
psycopg2-binary>=2.9.0
```

Update connection string:
```python
from src.database import init_db

db_url = "postgresql://user:password@host:5432/statarb"
db = init_db(db_url)
```

Docker Compose includes PostgreSQL service (uncomment to use).

## Monitoring & Maintenance

### Check Pipeline Status
```bash
# GitHub Actions
gh run list --workflow=daily_update.yml

# View specific run
gh run view RUN_ID --log
```

### Database Maintenance
```bash
# Backup SQLite
cp data/statarb.db data/statarb_backup.db

# Clear old signals
python -c "
from src.database import get_db_ops
from datetime import datetime, timedelta
db = get_db_ops()
# Custom cleanup logic
"
```

### Performance Monitoring
- Monitor Streamlit Cloud dashboard for resource usage
- Set up CloudWatch for AWS deployments
- Configure application logs

## Troubleshooting

### Streamlit Cloud Issues
- Check build logs in deployment settings
- Ensure all packages in requirements.txt are compatible
- Verify secrets are correctly set

### Data Sync Issues
- Ensure GitHub token has repo access
- Check GitHub Actions workflow permissions
- Verify git configuration

### Performance Issues
- Optimize data loading (use parquet files)
- Cache Streamlit computations
- Consider PostgreSQL for large databases

### Data Source Issues
- yfinance rate limits: add delays between requests
- NSE data availability: handle missing data gracefully
- Network timeouts: implement retry logic

## Production Checklist

- [ ] Database backed up
- [ ] Error logging configured
- [ ] Secrets securely managed
- [ ] GitHub Actions tested
- [ ] Data pipeline validated
- [ ] Streamlit settings optimized
- [ ] Rate limiting implemented
- [ ] Documentation updated
- [ ] Team trained on deployment process
- [ ] Monitoring setup complete

## Cost Estimates

**Streamlit Cloud (Free)**
- Free tier: 1 app, 1 GB storage, shared compute
- Pro: $5-15/month per app

**AWS Options**
- EC2 t3.micro: ~$10/month
- CloudRun: pay-per-use (~$0-10/month typical)

**Database**
- SQLite: Free (file-based)
- PostgreSQL RDS: ~$12-30/month

---

For additional help, check the main README.md or GitHub Issues.
