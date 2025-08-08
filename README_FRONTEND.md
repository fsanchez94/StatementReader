# PDF Bank Parser - Frontend Setup Guide

## Overview

This application now includes a modern web frontend built with React and Material-UI. The frontend provides a user-friendly interface for uploading PDF bank statements, selecting parsers, and downloading the processed CSV files.

## Architecture

- **Backend**: Flask REST API (Python) - Port 5000
- **Frontend**: React + Material-UI - Port 3000
- **Real-time Updates**: WebSockets via Socket.IO
- **File Processing**: Original Python parsers (maintained)

## Quick Start

### Option 1: Start Both Servers Automatically
```bash
python start_both.py
```

This will start both the API server (port 5000) and frontend server (port 3000).

### Option 2: Start Servers Separately

#### Start API Server:
```bash
python run_api.py
```

#### Start Frontend (in a new terminal):
```bash
python start_frontend.py
```

Or manually:
```bash
cd frontend
npm install
npm start
```

## Prerequisites

### Python Dependencies
```bash
pip install flask flask-cors flask-socketio werkzeug
```

### Node.js Dependencies
Make sure you have Node.js (14+) and npm installed:
- Download from: https://nodejs.org/

The frontend dependencies will be installed automatically when you run the start scripts.

## Using the Web Interface

1. **Access the Application**: Open http://localhost:3000 in your browser

2. **Upload Files**: 
   - Drag and drop PDF files or click to browse
   - Only PDF files are accepted

3. **Configure Parsers**:
   - Select the appropriate bank and account type for each file
   - Choose account holder (Husband/Spouse)

4. **Process Files**:
   - Click "Process Files" to start processing
   - Watch real-time progress updates

5. **Download Results**:
   - Download individual CSV files or combined file
   - View processing statistics and transaction counts

## API Endpoints

The Flask API provides the following endpoints:

- `GET /api/health` - Health check
- `GET /api/parser-types` - Available parser types
- `POST /api/upload` - Upload PDF files with parser configurations
- `POST /api/process/<job_id>` - Start processing uploaded files
- `GET /api/job/<job_id>` - Get job status and results
- `GET /api/download/<job_id>/<filename>` - Download processed files

## Features

### Web Interface Features
- **Drag & Drop Upload**: Modern file upload interface
- **Parser Selection**: Visual selection of bank and account types  
- **Real-time Progress**: Live updates during file processing
- **Results Dashboard**: Summary statistics and file download options
- **Error Handling**: Clear error messages and retry options
- **Responsive Design**: Works on desktop and mobile devices

### Technical Features
- **WebSocket Communication**: Real-time processing updates
- **File Upload Validation**: Only accepts PDF files
- **Job Management**: Track multiple processing jobs
- **Download Management**: Direct download of processed CSV files
- **Error Recovery**: Graceful handling of processing errors

## File Structure

```
pdf_bank_parser/
├── api/                    # Flask API backend
│   ├── app.py             # Main Flask application
│   └── __init__.py
├── frontend/              # React frontend
│   ├── public/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API and Socket services
│   │   ├── App.js         # Main App component
│   │   └── index.js       # Entry point
│   └── package.json       # Frontend dependencies
├── src/                   # Original Python parsers (unchanged)
├── run_api.py             # Start API server
├── start_frontend.py      # Start frontend server
├── start_both.py          # Start both servers
└── README_FRONTEND.md     # This file
```

## Development

### Running in Development Mode

Both servers run in development mode with hot reloading:
- API: Flask debug mode enabled
- Frontend: React development server with hot reload

### Customization

- **API Configuration**: Modify `api/app.py`
- **Frontend Styling**: Components use Material-UI theming
- **Parser Types**: Update the parser list in `api/app.py`

## Troubleshooting

### Common Issues

1. **Port Already in Use**: 
   - Change ports in the respective server files
   - Kill existing processes on ports 3000/5000

2. **Node.js Not Found**:
   - Install Node.js from https://nodejs.org/
   - Ensure npm is in your PATH

3. **API Connection Issues**:
   - Ensure API server is running on port 5000
   - Check firewall settings

4. **File Upload Issues**:
   - Verify file size limits
   - Ensure PDF files are not corrupted

### Development Tips

- Check browser developer console for frontend errors
- Check API server terminal for backend errors
- Use browser network tab to debug API requests

## Next Steps

The web interface is now ready for use! The original CLI scripts (`main.py`, `mainbundlev2.py`) continue to work alongside the new web interface.