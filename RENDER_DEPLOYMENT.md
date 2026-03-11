# Render Deployment Guide

## Prerequisites
- Render account (https://render.com)
- Git repository (GitHub, GitLab, Gitea)
- PostgreSQL database (Render provides this)
- Redis instance (Upstash, Redis Cloud, or similar)

## Step-by-Step Deployment

### 1. Add your code to a Git repository
```bash
git add .
git commit -m "Prepare for Render deployment"
git push
```

### 2. Connect your repository to Render

1. Go to https://render.com
2. Click "New +" and select "Web Service"
3. Connect your Git repository (GitHub/GitLab/Gitea)
4. Select the repository and branch

### 3. Configure the Web Service

**Basic Settings:**
- **Name**: `noavoice-livekit-backend`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --worker-class uvicorn.workers.UvicornWorker --workers 2 --timeout 120 --bind 0.0.0.0:$PORT main:app`
- **Plan**: Standard or higher (depending on traffic)

### 4. Set Environment Variables

Add these in the Render dashboard (Settings → Environment):

```
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(64))">
DATABASE_URL=<Your PostgreSQL connection string from Render>
REDIS_URL=<Your Redis connection string from Upstash or Redis Cloud>
GOOGLE_CLIENT_ID=<your-google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<your-google-oauth-secret>
GOOGLE_REDIRECT_URI=https://<your-render-url>.onrender.com/api/v1/auth/google/callback
CALCOM_API_KEY=<your-calcom-api-key>
CALCOM_EVENT_TYPE_ID=<your-calcom-event-type-id>
TWILIO_ACCOUNT_SID=<your-twilio-sid>
TWILIO_AUTH_TOKEN=<your-twilio-token>
TWILIO_PHONE_NUMBER=<your-twilio-number>
FRONTEND_URL=https://<your-frontend-url>
BASE_URL=https://<your-render-url>.onrender.com
DB_SCHEMA=noavoice_ns
AGENT_BASE_URL=<your-agent-url>
OPENWEATHER_API_KEY=<your-openweather-key>
```

### 5. Database Setup (PostgreSQL on Render)

1. Create a PostgreSQL database on Render
2. Copy the connection string as `DATABASE_URL`
3. Run migrations after first deployment:
   ```bash
   # Via Render shell or dashboard
   alembic upgrade head
   ```

### 6. Redis Setup

Use one of these options:
- **Upstash Redis** (Recommended, free tier available)
- **Redis Cloud**
- **Render Redis** (if available)

Copy the connection string as `REDIS_URL`

### 7. Custom Domain (Optional)

1. Go to Settings → Custom Domain in Render
2. Add your domain and follow DNS configuration instructions
3. Update `GOOGLE_REDIRECT_URI` and `BASE_URL` accordingly

## Production Checklist

- [ ] All environment variables set in Render dashboard
- [ ] Database URL configured and migrations run
- [ ] Redis URL configured
- [ ] Google OAuth secrets updated in Google Console (redirect URI)
- [ ] SECRET_KEY is strong (64+ characters)
- [ ] DEBUG is set to False
- [ ] ENVIRONMENT is set to production
- [ ] FRONTEND_URL points to production frontend
- [ ] BASE_URL points to your Render URL
- [ ] Health check endpoint returns 200 (https://your-url/health)

## Monitoring & Logs

1. View logs in Render dashboard: Settings → Logs
2. Monitor performance: Insights tab
3. Set up alerts for deployment failures

## Troubleshooting

### Application fails to start
- Check logs in Render dashboard
- Verify all required environment variables are set
- Ensure DATABASE_URL is correct
- Check that SECRET_KEY is at least 64 characters

### Database connection errors
- Verify DATABASE_URL format
- Ensure PostgreSQL service is running on Render
- Check IP allowlist if needed
- Run migrations: `alembic upgrade head`

### Health check failing
- Check that the app starts correctly
- Verify port binding to $PORT environment variable
- Check app logs for startup errors

### Redis connection issues
- Verify REDIS_URL format
- Check Redis service is running
- For Upstash, ensure default user is configured
- Test with: `redis-cli -u $REDIS_URL ping`

## Local Development with Docker

For local testing before deployment:

```bash
# Build and run locally
docker-compose up --build

# Access application
http://localhost:8000

# Run migrations
docker-compose exec web alembic upgrade head

# Stop services
docker-compose down
```

## Auto-Deploy Configuration

The `render.yaml` file enables automatic deployment on:
- Push to main branch
- New commits to connected branch

Modify `render.yaml` to change deployment settings.

## Scaling

As traffic grows, consider:
1. Upgrading plan (Standard → Pro → Business)
2. Increasing gunicorn workers (in Start Command)
3. Adding a caching layer
4. Database optimization

## Security Best Practices

- [ ] Rotate `SECRET_KEY` periodically
- [ ] Use strong database passwords
- [ ] Enable SSL for database connections
- [ ] Use HTTPS only (Render provides free SSL)
- [ ] Keep dependencies updated
- [ ] Monitor logs for suspicious activity
- [ ] Use IP allowlist if needed

## Performance Tips

1. **Database**: Add indexes for frequently queried columns
2. **Redis**: Use for session/cache storage
3. **Workers**: Adjust gunicorn workers based on load
4. **Timeouts**: Increase if jobs are timing out (120s default)
5. **Logging**: Monitor but don't log excessive data in production

## Rollback

If deployment has issues:
1. Render automatically keeps previous versions
2. Redeploy from previous build in dashboard
3. Or push a fix and redeploy

---

**Need help?** 
- Render Docs: https://render.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com
- Contact: support@render.com
