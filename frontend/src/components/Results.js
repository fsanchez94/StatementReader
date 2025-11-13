import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Grid,
  Card,
  CardContent,
  Alert,
  Chip,
  CircularProgress
} from '@mui/material';
import {
  CheckCircle,
  Download,
  Error,
  Assessment,
  TableChart,
  Refresh
} from '@mui/icons-material';
import { apiService } from '../services/api';

const Results = ({ job, onNewUpload }) => {
  const [availableFiles, setAvailableFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(false);

  useEffect(() => {
    // If job output files are missing, try to load available files
    if (!job?.outputFiles || job.outputFiles.length === 0) {
      loadAvailableFiles();
    }
  }, [job]);

  const loadAvailableFiles = async () => {
    try {
      setLoadingFiles(true);
      const filesData = await apiService.getAvailableFiles();
      setAvailableFiles(filesData.files || []);
    } catch (err) {
      console.error('Failed to load available files:', err);
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleDownload = async (filename) => {
    try {
      if (job?.id) {
        await apiService.downloadFile(job.id);
      } else {
        // Use direct download if no job ID
        await apiService.downloadFileDirect(filename);
      }
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  const getFileStatusIcon = (file) => {
    if (file.status === 'error' || file.error_message) {
      return <Error color="error" />;
    }
    if (file.status === 'completed') {
      return <CheckCircle color="success" />;
    }
    return <CheckCircle color="success" />;
  };

  const getFileStatusColor = (file) => {
    return file.status === 'error' ? 'error' : 'success';
  };

  const successfulFiles = job.results?.filter(f => f.status === 'completed') || [];
  const failedFiles = job.results?.filter(f => f.status === 'error') || [];
  const totalTransactions = job.totalTransactions || 0;

  return (
    <Box>
      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Assessment sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" color="primary">
                {totalTransactions}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Transacciones Totales
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <CheckCircle sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" color="success.main">
                {successfulFiles.length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Procesados Exitosamente
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Error sx={{ fontSize: 40, color: 'error.main', mb: 1 }} />
              <Typography variant="h4" color="error.main">
                {failedFiles.length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Fallidos al Procesar
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <TableChart sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h4" color="info.main">
                {job.outputFiles?.length || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Archivos de Salida
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Processing Results */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5">
            Resultados del Procesamiento
          </Typography>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={onNewUpload}
          >
            Procesar Más Archivos
          </Button>
        </Box>

        {/* Error Alert */}
        {failedFiles.length > 0 && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            {failedFiles.length} archivo{failedFiles.length > 1 ? 's' : ''} no se {failedFiles.length > 1 ? 'pudieron' : 'pudo'} procesar.
            Revisa la lista de archivos abajo para más detalles.
          </Alert>
        )}

        {/* File Results */}
        {job.results && job.results.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Detalles del Procesamiento de Archivos
            </Typography>
            <List>
              {job.results.map((file, index) => (
                <ListItem key={index} divider>
                  <ListItemIcon>
                    {getFileStatusIcon(file)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle2">
                          {file.filename}
                        </Typography>
                        <Chip 
                          label={file.account_holder} 
                          size="small" 
                          color="secondary"
                        />
                      </Box>
                    }
                    secondary={
                      file.error_message
                        ? `Error: ${file.error_message}`
                        : file.status === 'completed' ? 'Procesado exitosamente' : 'Procesando...'
                    }
                  />
                  <ListItemSecondaryAction>
                    <Chip
                      label={file.status === 'error' ? 'Fallido' : 'Éxito'}
                      color={getFileStatusColor(file)}
                      size="small"
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        <Divider sx={{ my: 3 }} />

        {/* Download Section */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Descargar Resultados
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Descarga los archivos CSV procesados que contienen tus datos de transacciones
          </Typography>

          {job?.outputFiles && job.outputFiles.length > 0 ? (
            <List>
              {job.outputFiles.map((file, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <TableChart color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary={file.filename}
                    secondary={`${file.transactions_count || 0} transactions • ${file.type || 'CSV'} file`}
                  />
                  <ListItemSecondaryAction>
                    <Button
                      variant="contained"
                      size="small"
                      startIcon={<Download />}
                      onClick={() => handleDownload(file.filename)}
                    >
                      Descargar
                    </Button>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          ) : loadingFiles ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <CircularProgress size={20} />
              <Typography>Cargando archivos disponibles...</Typography>
            </Box>
          ) : availableFiles.length > 0 ? (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                Datos del trabajo no disponibles, mostrando todos los archivos generados:
              </Alert>
              <List>
                {availableFiles.map((file, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <TableChart color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary={file.filename}
                      secondary={`${(file.size / 1024).toFixed(1)} KB • CSV file`}
                    />
                    <ListItemSecondaryAction>
                      <Button
                        variant="contained"
                        size="small"
                        startIcon={<Download />}
                        onClick={() => handleDownload(file.filename)}
                      >
                        Descargar
                      </Button>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Box>
          ) : (
            <Alert severity="info">
              No se generaron archivos de salida. Esto puede ocurrir si no se encontraron transacciones en los archivos procesados.
            </Alert>
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default Results;