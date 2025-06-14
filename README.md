# Feedback Catalyst

A web application that helps you turn raw feedback data into meaningful insights through automated analysis and visualization.

## Features

- Upload CSV and Excel files for analysis
- Auto-generated reports
- Smart sentiment analysis
- Visual rating insights
- Modern and responsive UI

## Tech Stack

- Frontend: React (functional components) + React Router
- Styling: CSS Modules
- Backend: Node.js + Express.js
- File Upload: Multer

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd feedback-catalyst
```

2. Install frontend dependencies:
```bash
cd client
npm install
```

3. Install backend dependencies:
```bash
cd ../server
npm install
```

## Running the Application

1. Start the backend server:
```bash
cd server
npm run dev
```
The server will start on http://localhost:5000

2. In a new terminal, start the frontend development server:
```bash
cd client
npm run dev
```
The frontend will start on http://localhost:5173

## File Upload

- Supported file types: .csv and .xlsx
- Maximum file size: 5MB
- Files are stored in the server's `uploads` directory

## Project Structure

```
feedback-catalyst/
├── client/                 # Frontend React application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── App.jsx       # Main App component
│   │   └── main.jsx      # Entry point
│   └── package.json
│
└── server/                # Backend Express application
    ├── uploads/          # Uploaded files directory
    ├── index.js         # Server entry point
    └── package.json
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. 