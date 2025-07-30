# MongoDB Atlas Setup Guide

## Environment Variables

Create a `.env` file in the server directory with the following variables:

```env
# MongoDB Atlas Connection
# Replace with your actual MongoDB Atlas connection string
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority

# Gemini API Key (optional - for AI features)
GEMINI_API_KEY=your_gemini_api_key_here
```

## MongoDB Atlas Connection String

Replace the placeholder in `MONGO_URI` with your actual MongoDB Atlas connection string:

1. **Get your connection string from MongoDB Atlas:**
   - Log into MongoDB Atlas
   - Go to your cluster
   - Click "Connect"
   - Choose "Connect your application"
   - Copy the connection string

2. **Replace the placeholders:**
   - `username`: Your MongoDB Atlas username
   - `password`: Your MongoDB Atlas password
   - `cluster.mongodb.net`: Your actual cluster URL
   - `database`: Your database name (will be created automatically)

## Example Connection String
```
MONGO_URI=mongodb+srv://myuser:mypassword123@cluster0.abc123.mongodb.net/feedback_db?retryWrites=true&w=majority
```

## Development vs Production

- **Development**: If `MONGO_URI` is not set, the app will use `mongodb://localhost:27017/`
- **Production**: Always set `MONGO_URI` to your MongoDB Atlas connection string

## Database Structure

The app will automatically create these collections in your database:
- `feedback_db` (database)
  - `files` (collection for uploaded files)
  - `charts` (collection for generated charts)
  - `fs.files` (GridFS collection for file storage)
  - `fs.chunks` (GridFS collection for file chunks)
  - `fs_charts.files` (GridFS collection for chart storage)
  - `fs_charts.chunks` (GridFS collection for chart chunks)

## Connection Status

The app will display connection status messages:
- ✅ MongoDB connection successful!
- ❌ MongoDB connection failed: [error details]
- ⚠️ MONGO_URI environment variable not found. Using localhost for development. 