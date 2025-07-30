import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import gridfs
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def connect_to_mongo():
    """
    Connect to MongoDB using environment variable MONGO_URI.
    Falls back to localhost for development if MONGO_URI is not set.
    """
    # Get MongoDB URI from environment variable
    mongo_uri = os.getenv('MONGO_URI')
    
    if not mongo_uri:
        print("⚠️  MONGO_URI environment variable not found. Using localhost for development.")
        print("   For production, set MONGO_URI to your MongoDB Atlas connection string.")
        mongo_uri = 'mongodb://localhost:27017/'
    
    try:
        # Connect to MongoDB with timeout
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        
        # Test the connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Get database and collections
        db = client['feedback_db']
        files_collection = db['files']
        charts_collection = db['charts']
        fs_files = gridfs.GridFS(db, collection='files')
        fs_charts = gridfs.GridFS(db, collection='charts')
        
        return client, db, files_collection, charts_collection, fs_files, fs_charts
        
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("   Please check your MongoDB Atlas cluster status and network access.")
        raise
    except ServerSelectionTimeoutError as e:
        print(f"❌ MongoDB server selection timeout: {e}")
        print("   Please check your MongoDB Atlas cluster status and connection string.")
        raise
    except Exception as e:
        print(f"❌ Unexpected MongoDB error: {e}")
        raise

# Initialize connection
try:
    client, db, files_collection, charts_collection, fs_files, fs_charts = connect_to_mongo()
except Exception as e:
    print(f"Failed to initialize MongoDB connection: {e}")
    # Set default values to prevent import errors
    client = None
    db = None
    files_collection = None
    charts_collection = None
    fs_files = None
    fs_charts = None 