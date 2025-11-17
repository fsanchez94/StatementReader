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
  Button,
  ThemeProvider,
  createTheme,
  CssBaseline
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

// Apple-inspired theme
const appleTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#007AFF',
      light: '#5AC8FA',
      dark: '#0051D5',
    },
    secondary: {
      main: '#5856D6',
    },
    success: {
      main: '#34C759',
      light: '#30D158',
    },
    error: {
      main: '#FF3B30',
      light: '#FF453A',
    },
    warning: {
      main: '#FF9500',
    },
    background: {
      default: '#FBFBFD',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1D1D1F',
      secondary: '#86868B',
    },
    divider: '#E5E5EA',
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"SF Pro Display"',
      '"SF Pro Text"',
      'system-ui',
      'Roboto',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '3rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
      lineHeight: 1.1,
    },
    h2: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
      lineHeight: 1.2,
    },
    h3: {
      fontSize: '2rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
      lineHeight: 1.2,
    },
    h4: {
      fontSize: '1.75rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
      lineHeight: 1.3,
    },
    h5: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.3,
    },
    h6: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    body1: {
      fontSize: '1.0625rem',
      lineHeight: 1.5,
      letterSpacing: '-0.01em',
    },
    body2: {
      fontSize: '0.9375rem',
      lineHeight: 1.5,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
      letterSpacing: '-0.01em',
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: [
    'none',
    '0px 1px 3px rgba(0, 0, 0, 0.04)',
    '0px 2px 8px rgba(0, 0, 0, 0.06)',
    '0px 4px 12px rgba(0, 0, 0, 0.08)',
    '0px 6px 16px rgba(0, 0, 0, 0.10)',
    '0px 8px 20px rgba(0, 0, 0, 0.12)',
    '0px 10px 24px rgba(0, 0, 0, 0.14)',
    '0px 12px 28px rgba(0, 0, 0, 0.16)',
    '0px 14px 32px rgba(0, 0, 0, 0.18)',
    '0px 16px 36px rgba(0, 0, 0, 0.20)',
    '0px 18px 40px rgba(0, 0, 0, 0.22)',
    '0px 20px 44px rgba(0, 0, 0, 0.24)',
    '0px 22px 48px rgba(0, 0, 0, 0.26)',
    '0px 24px 52px rgba(0, 0, 0, 0.28)',
    '0px 26px 56px rgba(0, 0, 0, 0.30)',
    '0px 28px 60px rgba(0, 0, 0, 0.32)',
    '0px 30px 64px rgba(0, 0, 0, 0.34)',
    '0px 32px 68px rgba(0, 0, 0, 0.36)',
    '0px 34px 72px rgba(0, 0, 0, 0.38)',
    '0px 36px 76px rgba(0, 0, 0, 0.40)',
    '0px 38px 80px rgba(0, 0, 0, 0.42)',
    '0px 40px 84px rgba(0, 0, 0, 0.44)',
    '0px 42px 88px rgba(0, 0, 0, 0.46)',
    '0px 44px 92px rgba(0, 0, 0, 0.48)',
    '0px 46px 96px rgba(0, 0, 0, 0.50)',
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          padding: '10px 20px',
          fontSize: '1.0625rem',
          fontWeight: 500,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
        contained: {
          '&:hover': {
            transform: 'translateY(-1px)',
            transition: 'all 0.2s ease',
          },
        },
        outlined: {
          borderWidth: '1.5px',
          '&:hover': {
            borderWidth: '1.5px',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        elevation1: {
          boxShadow: '0px 1px 3px rgba(0, 0, 0, 0.04)',
        },
        elevation2: {
          boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.06)',
        },
        elevation3: {
          boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.08)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(251, 251, 253, 0.72)',
          backdropFilter: 'blur(20px) saturate(180%)',
          borderBottom: '0.5px solid rgba(0, 0, 0, 0.08)',
          boxShadow: 'none',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
          borderRadius: 8,
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            fontWeight: 600,
            fontSize: '0.875rem',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          },
        },
      },
    },
  },
});

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
    <ThemeProvider theme={appleTheme}>
      <CssBaseline />
      <Router>
        <div className="App" style={{ minHeight: '100vh', backgroundColor: '#FBFBFD' }}>
          <AppBar position="sticky" elevation={0}>
            <Toolbar sx={{ py: 1 }}>
              <Typography
                variant="h6"
                component="div"
                sx={{
                  flexGrow: 1,
                  fontWeight: 600,
                  color: 'text.primary',
                  letterSpacing: '-0.02em'
                }}
              >
                Bank Statement Processor
              </Typography>
              <Button
                component={Link}
                to="/"
                startIcon={<UploadFileIcon />}
                sx={{
                  mr: 1.5,
                  color: 'text.primary',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  }
                }}
              >
                Upload
              </Button>
              <Button
                component={Link}
                to="/transactions"
                startIcon={<ListAltIcon />}
                sx={{
                  mr: 1.5,
                  color: 'text.primary',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  }
                }}
              >
                Transactions
              </Button>
              <Button
                component={Link}
                to="/account-holders"
                startIcon={<PeopleIcon />}
                sx={{
                  color: 'text.primary',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  }
                }}
              >
                Accounts
              </Button>
            </Toolbar>
          </AppBar>

          <Container maxWidth="lg" sx={{ mt: 5, mb: 8 }}>
            {error && (
              <Alert
                severity="error"
                sx={{
                  mb: 4,
                  borderRadius: 2,
                  border: '1px solid',
                  borderColor: 'error.light',
                }}
                onClose={() => setError(null)}
              >
                {error}
              </Alert>
            )}

            <Routes>
              <Route path="/" element={
                !currentJob ? (
                  <Paper
                    elevation={2}
                    sx={{
                      p: 5,
                      borderRadius: 3,
                    }}
                  >
                    <Typography variant="h3" gutterBottom sx={{ mb: 2 }}>
                      Upload Bank Statements
                    </Typography>
                    <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 4, fontSize: '1.0625rem' }}>
                      Upload your bank statements in PDF format and select the appropriate processor for each file.
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
                )
              } />
              <Route path="/transactions" element={<TransactionsList />} />
              <Route path="/account-holders" element={<AccountHolderManagement />} />
            </Routes>
          </Container>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;