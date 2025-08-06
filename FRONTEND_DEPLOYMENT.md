# Frontend Deployment Guide for Vercel

## 🚀 Deploying React Frontend to Vercel

### Prerequisites
1. **Vercel Account** - For hosting
2. **GitHub Repository** - For code deployment
3. **Deployed Backend** - Your Render backend URL

### Step 1: Update Backend URL

Before deploying, update the backend URL in your configuration:

1. **Update API Configuration**
   - Edit `client/src/config/api.js`
   - Replace the default URL with your deployed backend URL:
   ```javascript
   const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://your-backend-app-name.onrender.com';
   ```

2. **Set Environment Variable (Optional)**
   - In Vercel dashboard, add environment variable:
   ```
   VITE_API_BASE_URL=https://your-backend-app-name.onrender.com
   ```

### Step 2: Vercel Deployment

1. **Connect GitHub Repository**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Project Settings**
   - **Framework Preset**: Vite
   - **Root Directory**: `client`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

3. **Environment Variables**
   - Add in Vercel dashboard:
   ```
   VITE_API_BASE_URL=https://your-backend-app-name.onrender.com
   ```

4. **Deploy**
   - Click "Deploy"
   - Vercel will automatically build and deploy your app

### Step 3: Verify Deployment

1. **Check Build Logs**
   - Ensure build completes successfully
   - Check for any dependency issues

2. **Test Functionality**
   - Test file upload
   - Test report generation
   - Test chart viewing
   - Test suggestions download

3. **Check API Calls**
   - Open browser developer tools
   - Check Network tab for API calls
   - Ensure calls go to your Render backend

### Step 4: Custom Domain (Optional)

1. **Add Custom Domain**
   - In Vercel dashboard, go to "Settings" → "Domains"
   - Add your custom domain
   - Configure DNS settings

2. **SSL Certificate**
   - Vercel provides automatic SSL
   - No additional configuration needed

### Troubleshooting

#### Common Issues:

1. **Build Fails**
   - Check `package.json` has all dependencies
   - Ensure Node.js version is compatible
   - Check for TypeScript errors

2. **API Calls Fail**
   - Verify backend URL is correct
   - Check CORS configuration on backend
   - Ensure backend is running

3. **Environment Variables**
   - Verify `VITE_API_BASE_URL` is set correctly
   - Check variable name starts with `VITE_`
   - Redeploy after changing environment variables

4. **CORS Errors**
   - Backend CORS is configured for all origins (`*`)
   - Check if backend URL is correct
   - Ensure backend is accessible

#### Debugging Steps:

1. **Check Console Logs**
   - Open browser developer tools
   - Check Console for errors
   - Check Network tab for failed requests

2. **Verify API Endpoints**
   - Test backend health: `https://your-backend.onrender.com/health`
   - Check if all endpoints are accessible

3. **Environment Variables**
   - Add console.log to check API_BASE_URL
   - Verify environment variable is loaded

### File Structure for Frontend Deployment

```
client/
├── src/
│   ├── components/
│   │   ├── Report/
│   │   ├── Header/
│   │   ├── Hero/
│   │   ├── Features/
│   │   ├── HowItWorks/
│   │   └── Footer/
│   ├── config/
│   │   └── api.js          # API configuration
│   ├── App.jsx
│   └── main.jsx
├── public/
├── package.json
├── vite.config.js
├── vercel.json             # Vercel configuration
└── .gitignore
```

### Environment Variables

#### Required:
- `VITE_API_BASE_URL` - Your deployed backend URL

#### Optional:
- `VITE_APP_NAME` - Application name
- `VITE_APP_VERSION` - Application version

### Security Notes

1. **Environment Variables**: Only variables starting with `VITE_` are exposed to frontend
2. **API Keys**: Never expose backend API keys in frontend
3. **CORS**: Backend allows all origins for development
4. **HTTPS**: Vercel provides automatic HTTPS

### Performance Optimization

1. **Build Optimization**: Vite automatically optimizes builds
2. **CDN**: Vercel provides global CDN
3. **Caching**: Automatic caching for static assets
4. **Image Optimization**: Vercel optimizes images automatically

### Next Steps

1. **Deploy Frontend**: Follow the steps above
2. **Test Integration**: Ensure frontend connects to backend
3. **Monitor Performance**: Use Vercel analytics
4. **Set Up Monitoring**: Consider error tracking (Sentry)

### Support

- **Vercel Docs**: https://vercel.com/docs
- **Vite Docs**: https://vitejs.dev
- **React Docs**: https://reactjs.org

### Quick Deployment Checklist

- [ ] Update backend URL in `client/src/config/api.js`
- [ ] Remove proxy from `package.json`
- [ ] Push code to GitHub
- [ ] Connect repository to Vercel
- [ ] Set environment variables
- [ ] Deploy
- [ ] Test all functionality
- [ ] Verify API calls work
- [ ] Check for console errors
