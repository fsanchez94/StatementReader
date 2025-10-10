import React, { useState, useEffect } from 'react';
import {
  Container,
  AppBar,
  Toolbar,
  Typography,
  Box,
  Paper,
  Alert
} from '@mui/material';
import FileUpload from './components/FileUpload';
import ProcessingStatus from './components/ProcessingStatus';
import Results from './components/Results';
import { apiService } from './services/api';
import { socketService } from './services/socket';

function App() {
  const [currentJob, setCurrentJob] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [parserTypes, setParserTypes] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load parser types on app start
    loadParserTypes();
    
    // Setup socket listeners (disabled for now - Django backend doesn't use WebSocket)
    // socketService.connect();
    
    // socketService.onJobStatus((data) => {
    //   if (data.status === 'processing') {
    //     setProcessing(true);
    //   }
    // });

    // socketService.onJobProgress((data) => {
    //   setCurrentJob(prev => ({
    //     ...prev,
    //     progress: data.progress,
    //     currentFile: data.current_file
    //   }));
    // });

    // socketService.onJobCompleted((data) => {
    //   setProcessing(false);
    //   setCurrentJob(prev => ({
    //     ...prev,
    //     status: 'completed',
    //     results: data.results,
    //     outputFiles: data.output_files,
    //     totalTransactions: data.total_transactions
    //   }));
    // });

    // socketService.onJobError((data) => {
    //   setProcessing(false);
    //   setError(`Processing error: ${data.error}`);
    // });

    return () => {
      // socketService.disconnect();
    };
  }, []);

  const loadParserTypes = async () => {
    try {
      const types = await apiService.getParserTypes();
      setParserTypes(types);
    } catch (err) {
      setError('Failed to load parser types');
      console.error(err);
    }
  };

  const handleFilesUploaded = async (sessionId) => {
    try {
      console.log('Starting file processing for session:', sessionId);
      setCurrentJob({ id: sessionId, status: 'uploaded' });
      setProcessing(true);
      setError(null);
      
      // Start processing
      setCurrentJob(prev => ({ ...prev, status: 'processing' }));
      console.log('Calling processSession API...');
      const result = await apiService.processSession(sessionId);
      console.log('Process result:', result);
      
      setProcessing(false);
      
      if (result.status === 'completed') {
        console.log('Processing completed successfully');
        setCurrentJob(prev => ({
          ...prev,
          status: 'completed',
          results: result.files,
          outputFiles: result.output_file ? [{ filename: result.output_file }] : [],
          totalTransactions: result.files ? result.files.length : 0
        }));
      } else {
        console.log('Processing completed but status is:', result.status);
        setError(`Processing completed but status is: ${result.status}`);
        setCurrentJob(prev => ({ ...prev, status: 'error' }));
      }
    } catch (err) {
      setProcessing(false);
      setError(`Failed to process files: ${err.message}`);
      setCurrentJob(prev => ({ ...prev, status: 'error' }));
      console.error('Processing error:', err);
    }
  };

  const handleNewUpload = () => {
    setCurrentJob(null);
    setProcessing(false);
    setError(null);
  };

  return (
    <div className="App">
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            PDF Bank Statement Parser
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {!currentJob ? (
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
              Upload Bank Statements
            </Typography>
            <Typography variant="body1" color="textSecondary" paragraph>
              Upload your PDF bank statements and select the appropriate parser for each file.
              The system supports multiple Guatemalan banks including Banco Industrial, BAM, and GyT.
            </Typography>
            <FileUpload 
              parserTypes={parserTypes}
              onFilesUploaded={handleFilesUploaded}
            />
          </Paper>
        ) : (
          <Box>
            {(processing || currentJob.status === 'processing') && (
              <ProcessingStatus job={currentJob} />
            )}
            
            {currentJob.status === 'completed' && (
              <Results 
                job={currentJob}
                onNewUpload={handleNewUpload}
              />
            )}
          </Box>
        )}
      </Container>
    </div>
  );
}

export default App;