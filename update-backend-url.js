#!/usr/bin/env node

/**
 * Script to update the backend URL in the frontend configuration
 * Usage: node update-backend-url.js <your-backend-url>
 * Example: node update-backend-url.js https://feedback-catalyst-server.onrender.com
 */

const fs = require('fs');
const path = require('path');

function updateBackendUrl(newUrl) {
  const configPath = path.join(__dirname, 'client', 'src', 'config', 'api.js');
  
  try {
    // Read the current configuration
    let content = fs.readFileSync(configPath, 'utf8');
    
    // Update the default URL
    const updatedContent = content.replace(
      /const API_BASE_URL = import\.meta\.env\.VITE_API_BASE_URL \|\| 'https:\/\/your-backend-app-name\.onrender\.com';/,
      `const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '${newUrl}';`
    );
    
    // Write the updated content
    fs.writeFileSync(configPath, updatedContent);
    
    console.log('✅ Backend URL updated successfully!');
    console.log(`📝 Updated to: ${newUrl}`);
    console.log('\n📋 Next steps:');
    console.log('1. Commit and push your changes to GitHub');
    console.log('2. Deploy to Vercel');
    console.log('3. Set VITE_API_BASE_URL environment variable in Vercel dashboard');
    
  } catch (error) {
    console.error('❌ Error updating backend URL:', error.message);
    process.exit(1);
  }
}

// Get the backend URL from command line arguments
const backendUrl = process.argv[2];

if (!backendUrl) {
  console.log('❌ Please provide your backend URL');
  console.log('Usage: node update-backend-url.js <your-backend-url>');
  console.log('Example: node update-backend-url.js https://feedback-catalyst-server.onrender.com');
  process.exit(1);
}

// Validate URL format
if (!backendUrl.startsWith('http://') && !backendUrl.startsWith('https://')) {
  console.log('❌ Please provide a valid URL starting with http:// or https://');
  process.exit(1);
}

updateBackendUrl(backendUrl);
