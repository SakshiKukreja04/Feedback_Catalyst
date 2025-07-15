# Flask API Debug Guide

This guide will help you fix the 500 Internal Server Error and CORS issues with your Flask API.

## 🔧 **Step 1: Install Dependencies**

```bash
pip install -r requirements.txt
```

## 🔧 **Step 2: Create .env File**

Create a `.env` file in the server directory with your MongoDB Atlas connection string:

```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
```

**Replace with your actual MongoDB Atlas URI:**
1. Go to MongoDB Atlas dashboard
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Copy the connection string
5. Replace `<username>`, `<password>`, and `<database>` with your actual values

## 🔧 **Step 3: Test Your Setup**

Run the comprehensive debug script:

```bash
python debug_setup.py
```

This will test:
- ✅ Environment variables
- ✅ Dependencies
- ✅ MongoDB Atlas connection
- ✅ Flask server
- ✅ CORS configuration
- ✅ File upload functionality

## 🔧 **Step 4: Start the Server**

```bash
python app.py
```

## 🔧 **Step 5: Test from Frontend**

Your React frontend should now work correctly. The server will:

- ✅ Handle CORS automatically
- ✅ Connect to MongoDB Atlas
- ✅ Validate file uploads
- ✅ Provide detailed error messages

## 🐛 **Common Issues & Solutions**

### **Issue 1: "MONGODB_URI not found"**
**Solution:** Create a `.env` file with your MongoDB Atlas URI

### **Issue 2: "MongoDB connection failed"**
**Solutions:**
- Check your MongoDB Atlas connection string
- Ensure your IP is whitelisted in Atlas
- Verify username/password are correct

### **Issue 3: "CORS error"**
**Solution:** The updated code handles CORS automatically with flask-cors

### **Issue 4: "500 Internal Server Error"**
**Solutions:**
- Check server logs for detailed error messages
- Ensure MongoDB Atlas is accessible
- Verify file format is supported (.csv, .xlsx, .xls)

## 📋 **What Was Fixed**

### ✅ **Environment Variables**
- Added `python-dotenv` for `.env` file support
- Proper environment variable loading

### ✅ **MongoDB Connection**
- Better error handling for Atlas connections
- Connection retry logic
- Detailed logging for debugging

### ✅ **CORS Configuration**
- Removed manual CORS headers (conflicting with flask-cors)
- Let flask-cors handle all CORS automatically

### ✅ **Error Handling**
- Comprehensive logging
- File validation before processing
- Better error messages

### ✅ **File Upload**
- File type validation
- File content validation with pandas
- Detailed response with file info

## 🧪 **Testing Your Setup**

1. **Test server health:**
   ```bash
   curl http://localhost:5001/test
   ```

2. **Test file upload:**
   ```bash
   python debug_setup.py
   ```

3. **Test from browser:**
   - Visit `http://localhost:5001/test`
   - Should see JSON response with MongoDB status

## 📊 **Expected Responses**

### **Server Health Check:**
```json
{
  "message": "Server is running!",
  "status": "ok",
  "mongodb_connected": true,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### **Successful File Upload:**
```json
{
  "filename": "test.csv",
  "id": "507f1f77bcf86cd799439011",
  "file_size": 1024,
  "columns": 3
}
```

## 🚨 **If Still Having Issues**

1. **Check server logs** - Look for detailed error messages
2. **Test MongoDB connection** - Use the debug script
3. **Verify .env file** - Ensure MONGODB_URI is set correctly
4. **Check network** - Ensure you can reach MongoDB Atlas

The updated code includes comprehensive logging, so check the console output for specific error messages. 