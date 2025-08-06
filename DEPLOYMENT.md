# Deployment Guide for Feedback Catalyst

## 🚀 Deploying to Render

### Prerequisites
1. **MongoDB Atlas Account** - For database
2. **Render Account** - For hosting
3. **GitHub Repository** - For code deployment

### Step 1: MongoDB Atlas Setup

1. **Create MongoDB Atlas Cluster**
   - Go to [MongoDB Atlas](https://cloud.mongodb.com)
   - Create a new cluster (free tier is fine)
   - Set up database access (create a user)
   - Set up network access (allow all IPs: 0.0.0.0/0)

2. **Get Connection String**
   - In your cluster, click "Connect"
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password

### Step 2: Render Deployment

1. **Connect GitHub Repository**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Environment Variables**
   - In your Render service settings, add these environment variables:
   
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/feedback_db?retryWrites=true&w=majority
   ```

3. **Build Settings**
   - **Build Command**: `pip install -r server/requirements.txt`
   - **Start Command**: `cd server && gunicorn app:app --bind 0.0.0.0:$PORT`

### Step 3: Environment Variables

#### Required Environment Variables:
- `GEMINI_API_KEY` - Your Google Gemini API key
- `MONGO_URI` - MongoDB Atlas connection string
- `PORT` - Automatically set by Render

#### Optional Environment Variables:
- `PYTHON_VERSION` - Set to 3.9.16 (already in runtime.txt)

### Step 4: Verify Deployment

1. **Health Check**
   - Visit: `https://your-app-name.onrender.com/health`
   - Should return: `{"status": "healthy", "message": "Server is running"}`

2. **Test API Endpoints**
   - Test file upload: `/upload`
   - Test headers: `/headers/<filename>`
   - Test report generation: `/api/generate-stakeholder-report`

### Step 5: Frontend Configuration

Update your frontend to use the Render URL:
```javascript
// Replace localhost:5001 with your Render URL
const API_BASE_URL = 'https://your-app-name.onrender.com';
```

### Troubleshooting

#### Common Issues:

1. **Build Fails**
   - Check requirements.txt has all dependencies
   - Ensure Python version is compatible

2. **Database Connection Fails**
   - Verify MONGO_URI is correct
   - Check MongoDB Atlas network access
   - Ensure database user has correct permissions

3. **CORS Errors**
   - CORS is configured to allow all origins (`*`)
   - Check if frontend is using correct API URL

4. **API Key Issues**
   - Verify GEMINI_API_KEY is set correctly
   - Check if API key has proper permissions

#### Logs and Debugging:
- Check Render logs in the dashboard
- Use `/health` endpoint to verify server status
- Monitor MongoDB Atlas logs for database issues

### File Structure for Deployment

```
├── server/
│   ├── app.py                 # Main Flask application
│   ├── requirements.txt       # Python dependencies
│   ├── feedback_processor.py  # Core processing logic
│   └── database.py           # MongoDB configuration
├── client/                   # Frontend (deploy separately)
├── render.yaml              # Render configuration
├── Procfile                 # Process definition
├── runtime.txt              # Python version
└── .gitignore              # Git exclusions
```

### Security Notes

1. **Environment Variables**: Never commit API keys to Git
2. **CORS**: Currently allows all origins for development
3. **Database**: Use MongoDB Atlas for production
4. **Logs**: Monitor application logs for errors

### Performance Optimization

1. **Database**: Use MongoDB Atlas for scalability
2. **Caching**: Consider Redis for session storage
3. **CDN**: Use Cloudflare for static assets
4. **Monitoring**: Set up alerts for errors

### Next Steps

1. **Deploy Backend**: Follow the steps above
2. **Deploy Frontend**: Deploy React app to Vercel/Netlify
3. **Configure Domain**: Set up custom domain
4. **SSL**: Render provides automatic SSL
5. **Monitoring**: Set up error tracking (Sentry)

### Support

- **Render Docs**: https://render.com/docs
- **MongoDB Atlas**: https://docs.atlas.mongodb.com
- **Flask Docs**: https://flask.palletsprojects.com
