# Feedback Analysis Server

A Flask-based API server for processing feedback data and generating reports with charts.

## Features

- Upload Excel/CSV files and store in MongoDB GridFS
- Generate stakeholder and subject feedback reports
- Create interactive charts with proper label formatting
- Export reports as PDF with embedded charts
- AI-powered suggestion summarization using Gemini

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. MongoDB Configuration

#### For Development (Local MongoDB)
The app will automatically use `mongodb://localhost:27017/` if no environment variable is set.

#### For Production (MongoDB Atlas)
1. Create a `.env` file in the server directory
2. Add your MongoDB Atlas connection string:

```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
```

See `MONGODB_SETUP.md` for detailed setup instructions.

### 3. Environment Variables

Create a `.env` file with the following variables:

```env
# MongoDB Atlas Connection (required for production)
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority

# Gemini API Key (optional - for AI features)
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Test Connection

```bash
# Test local MongoDB connection
python app.py

# Test MongoDB Atlas connection (after setting MONGO_URI)
python test_mongodb_atlas.py
```

## Running the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

- `POST /upload` - Upload Excel/CSV files
- `GET /headers/<filename>` - Get column headers from uploaded file
- `POST /generate-report` - Generate PDF reports
- `POST /generate-charts` - Generate charts for viewing
- `GET /charts/<filename>` - Get generated chart images
- `POST /get-suggestions` - Get AI-powered suggestion summaries

## Database Structure

The app automatically creates these collections:
- `feedback_db` (database)
  - `files` - Uploaded file metadata
  - `charts` - Generated chart metadata
  - `fs.files` & `fs.chunks` - GridFS for file storage
  - `fs_charts.files` & `fs_charts.chunks` - GridFS for chart storage

## Connection Status

The app displays connection status messages:
- ✅ MongoDB connection successful!
- ❌ MongoDB connection failed: [error details]
- ⚠️ MONGO_URI environment variable not found. Using localhost for development.

## Development vs Production

- **Development**: Uses localhost MongoDB (no setup required)
- **Production**: Requires MongoDB Atlas connection string in `MONGO_URI`

## Troubleshooting

1. **Connection Issues**: Check `MONGODB_SETUP.md` for detailed setup instructions
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **Environment Variables**: Ensure `.env` file is in the server directory
4. **Port Conflicts**: Change port in `app.py` if needed

## Files

- `app.py` - Main Flask application
- `feedback_processor.py` - Core processing logic
- `database.py` - MongoDB connection management
- `MONGODB_SETUP.md` - Detailed MongoDB Atlas setup guide
- `test_mongodb_atlas.py` - Connection testing script 