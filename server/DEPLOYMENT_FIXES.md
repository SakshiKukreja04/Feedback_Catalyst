# Deployment Fixes for CORS and Memory Issues

## Issues Fixed

### 1. CORS Configuration
- **Problem**: Frontend at `https://feedback-catalyst.vercel.app` couldn't access backend at `https://feedback-catalyst.onrender.com`
- **Solution**: Updated CORS to use environment variable `VITE_FRONTEND_BASE_URL`

### 2. Memory Issues
- **Problem**: Worker timeout and memory errors during PDF generation
- **Solution**: 
  - Added memory optimization in PDF processing
  - Increased Gunicorn timeout to 5 minutes
  - Added memory monitoring

### 3. Worker Timeout
- **Problem**: Processes taking too long to complete
- **Solution**: Created `gunicorn.conf.py` with proper timeout settings

## Environment Variables Required

Set these in your Render deployment:

```bash
VITE_FRONTEND_BASE_URL=https://feedback-catalyst.vercel.app
```

## Deployment Steps

1. **Update Environment Variables**:
   - Go to your Render dashboard
   - Navigate to your service
   - Add environment variable: `VITE_FRONTEND_BASE_URL=https://feedback-catalyst.vercel.app`

2. **Deploy with Gunicorn Config**:
   ```bash
   gunicorn -c gunicorn.conf.py app:app
   ```

3. **Test CORS**:
   ```bash
   python test_cors.py
   ```

## Memory Optimization Features

- **Streaming Processing**: Files are processed one by one instead of loading all into memory
- **Immediate Cleanup**: Memory is freed immediately after each file processing
- **Error Handling**: Individual file failures don't stop the entire process
- **Memory Monitoring**: Logs memory usage at each stage for debugging

## Monitoring

The app now logs:
- CORS configuration on startup
- Memory usage at each stage
- File processing progress
- Error details for individual files

## Expected Behavior

- ✅ CORS should allow requests from `https://feedback-catalyst.vercel.app`
- ✅ Memory usage should stay stable during PDF generation
- ✅ Timeout should be 5 minutes instead of default 30 seconds
- ✅ Individual file failures won't crash the entire process
