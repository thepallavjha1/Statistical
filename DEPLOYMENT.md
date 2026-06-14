# Deployment Guide

## Prerequisites
- GitHub account
- Streamlit Cloud account (free)
- Python 3.8+

## Option 1: Deploy to Streamlit Cloud (Recommended)

### Step 1: Prepare Repository
```bash
# Ensure requirements.txt is up to date
pip freeze > requirements.txt

# Create .streamlit directory
mkdir -p .streamlit

# Create config.toml
cat > .streamlit/config.toml << EOF
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#0e1117"
secondaryBackgroundColor = "#161b22"
textColor = "#c9d1d9"
font = "sans serif"

[server]
headless = true
port = 8501
EOF

# Ensure secrets.toml is in .gitignore
echo ".streamlit/secrets.toml" >> .gitignore
```

### Step 2: Push to GitHub
```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### Step 3: Deploy on Streamlit Cloud
1. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
2. Click "New app"
3. Select your repository
4. Select main branch
5. Set main file path: `streamlit_app/app.py`
6. Click "Deploy"

### Step 4: Configure Secrets
1. In Streamlit Cloud dashboard, click "Advanced settings"
2. Add secrets:
   ```
   DB_PATH = "data/statarb.db"
   DATA_DIR = "data/"
   ```

### Step 5: Enable GitHub Integration
1. Go to app settings
2. Enable GitHub Action on push
3. Pipeline runs automatically on commits

## Option 2: Docker Deployment

### Build Docker Image
```bash
docker build -t statarb-platform:latest .
```

### Run Locally
```bash
docker run -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -e DB_PATH=/app/data/statarb.db \
  statarb-platform:latest
```

### Docker Compose
```bash
docker-compose up -d

# Check logs
docker-compose logs -f statarb-app

# Stop
docker-compose down
```

## Option 3: AWS Deployment

### Using CloudRun
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT/statarb-platform

# Deploy
gcloud run deploy statarb-platform \
  --image gcr.io/YOUR_PROJECT/statarb-platform \
  --platform managed \
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
