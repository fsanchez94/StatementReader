import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import {
  Container,
  AppBar,
  Toolbar,
  Typography,
  Box,
  Paper,
  Alert,
  Button
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import ListAltIcon from '@mui/icons-material/ListAlt';
import PeopleIcon from '@mui/icons-material/People';
import FileUpload from './components/FileUpload';
import ProcessingStatus from './components/ProcessingStatus';
import Results from './components/Results';
import TransactionsList from './components/TransactionsList';
import AccountHolderManagement from './components/AccountHolderManagement';
import { apiService } from './services/api';

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
      setError('Error al cargar tipos de procesadores');
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
        setError(`Procesamiento completado pero el estado es: ${result.status}`);
        setCurrentJob(prev => ({ ...prev, status: 'error' }));
      }
    } catch (err) {
      setProcessing(false);
      setError(`Error al procesar archivos: ${err.message}`);
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
    <Router>
      <div className="App">
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Procesador de Estados de Cuenta Bancarios
            </Typography>
            <Button
              color="inherit"
              component={Link}
              to="/"
              startIcon={<UploadFileIcon />}
              sx={{ mr: 2 }}
            >
              Subir Archivo
            </Button>
            <Button
              color="inherit"
              component={Link}
              to="/transactions"
              startIcon={<ListAltIcon />}
              sx={{ mr: 2 }}
            >
              Transacciones
            </Button>
            <Button
              color="inherit"
              component={Link}
              to="/account-holders"
              startIcon={<PeopleIcon />}
            >
              Titulares
            </Button>
          </Toolbar>
        </AppBar>

        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Routes>
            <Route path="/" element={
              !currentJob ? (
                <Paper elevation={3} sx={{ p: 3 }}>
                  <Typography variant="h4" gutterBottom>
                    Subir Estados de Cuenta
                  </Typography>
                  <Typography variant="body1" color="textSecondary" paragraph>
                    Sube tus estados de cuenta bancarios en PDF y selecciona el procesador apropiado para cada archivo.
                    El sistema soporta múltiples bancos guatemaltecos incluyendo Banco Industrial, BAM y GyT.
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
              )
            } />
            <Route path="/transactions" element={<TransactionsList />} />
            <Route path="/account-holders" element={<AccountHolderManagement />} />
          </Routes>
        </Container>
      </div>
    </Router>
  );
}

export default App;