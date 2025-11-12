import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Grid,
  Alert,
  LinearProgress,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  CloudUpload,
  Delete,
  PictureAsPdf,
  Assignment,
  AutoAwesome,
  CheckCircle
} from '@mui/icons-material';
import { apiService } from '../services/api';

const FileUpload = ({ parserTypes, onFilesUploaded }) => {
  const [files, setFiles] = useState([]);
  const [parserSelections, setParserSelections] = useState({});
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [autoDetecting, setAutoDetecting] = useState(false);
  const [autoSuggestions, setAutoSuggestions] = useState({});
  const [sessionId, setSessionId] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const validFiles = acceptedFiles.filter(file => {
      const name = file.name.toLowerCase();
      const isPdf = file.type === 'application/pdf' || name.endsWith('.pdf');
      const isCsv = file.type === 'text/csv' || name.endsWith('.csv');
      return isPdf || isCsv;
    });

    if (validFiles.length !== acceptedFiles.length) {
      setError('Solo se aceptan archivos PDF y CSV');
      return;
    }

    setFiles(prev => [...prev, ...validFiles]);
    setError(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/csv': ['.csv']
    },
    multiple: true
  });

  const removeFile = (index) => {
    const fileToRemove = files[index];
    setFiles(prev => prev.filter((_, i) => i !== index));
    
    // Remove parser selection for this file
    setParserSelections(prev => {
      const updated = { ...prev };
      delete updated[fileToRemove.name];
      return updated;
    });
    
  };

  const handleParserChange = (filename, parserId) => {
    const parser = parserTypes.find(p => p.id === parserId);
    setParserSelections(prev => ({
      ...prev,
      [filename]: {
        bank: parser.bank,
        account: parser.account,
        label: parser.label,
        isAutoSuggested: false
      }
    }));
  };


  const canUpload = () => {
    if (files.length === 0) return false;
    
    // Check that all files have parser selections
    return files.every(file => 
      parserSelections[file.name]
    );
  };

  const handleAutoDetect = async () => {
    if (files.length === 0) {
      setError('Por favor agrega archivos primero');
      return;
    }

    // If no session exists, upload files first
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      setAutoDetecting(true);
      setError(null);
      
      try {
        const uploadResult = await apiService.uploadFiles(files, {});
        currentSessionId = uploadResult.session_id;
        setSessionId(currentSessionId);
      } catch (err) {
        setError(`Error al subir: ${err.message}`);
        setAutoDetecting(false);
        return;
      }
    }

    setAutoDetecting(true);
    setError(null);

    try {
      const result = await apiService.detectParserTypes(currentSessionId);
      setAutoSuggestions(result.results);
      
      // Apply suggestions to parser selections
      const newSelections = { ...parserSelections };
      Object.keys(result.results).forEach(filename => {
        const suggestion = result.results[filename];
        if (suggestion.suggested) {
          newSelections[filename] = {
            ...suggestion.suggested,
            isAutoSuggested: true
          };
        }
      });
      setParserSelections(newSelections);
    } catch (err) {
      setError(`Error en auto-detección: ${err.message}`);
      console.error(err);
    } finally {
      setAutoDetecting(false);
    }
  };

  const handleUpload = async () => {
    if (!canUpload()) {
      setError('Por favor selecciona procesador para todos los archivos');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      if (sessionId) {
        // Files already uploaded, update parser selections and proceed to processing
        await apiService.updateParserSelections(sessionId, parserSelections);
        onFilesUploaded(sessionId);
      } else {
        // Upload files with configurations
        const result = await apiService.uploadFiles(files, parserSelections);
        setSessionId(result.session_id);
        onFilesUploaded(result.session_id);
      }
    } catch (err) {
      setError(`Upload failed: ${err.message}`);
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* File Drop Zone */}
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          border: 2,
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          borderStyle: 'dashed',
          borderRadius: 2,
          textAlign: 'center',
          cursor: 'pointer',
          mb: 3,
          transition: 'border-color 0.3s ease',
          '&:hover': {
            borderColor: 'primary.main',
          },
        }}
        elevation={0}
      >
        <input {...getInputProps()} />
        <CloudUpload sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Suelta archivos PDF o CSV aquí' : 'Arrastra archivos PDF o CSV aquí'}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          o haz clic para buscar archivos
        </Typography>
        <Button variant="outlined" sx={{ mt: 2 }}>
          Buscar Archivos
        </Button>
      </Paper>

      {/* File List */}
      {files.length > 0 && (
        <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Archivos Seleccionados ({files.length})
          </Typography>
          
          <List>
            {files.map((file, index) => {
              const isCSV = file.name.toLowerCase().endsWith('.csv');
              const FileIcon = isCSV ? Assignment : PictureAsPdf;
              const iconColor = isCSV ? 'success.main' : 'error.main';

              return (
                <ListItem key={index} divider>
                  <FileIcon sx={{ mr: 2, color: iconColor }} />
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {file.name}
                        <Chip
                          label={isCSV ? 'CSV' : 'PDF'}
                          size="small"
                          color={isCSV ? 'success' : 'error'}
                          variant="outlined"
                        />
                      </Box>
                    }
                    secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={() => removeFile(index)}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              );
            })}
          </List>
        </Paper>
      )}

      {/* Parser Selection */}
      {files.length > 0 && (
        <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6" gutterBottom sx={{ mb: 0 }}>
                <Assignment sx={{ mr: 1, verticalAlign: 'middle' }} />
                Configurar Procesadores
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Selecciona el banco y tipo de cuenta apropiado para cada archivo
              </Typography>
            </Box>
            <Tooltip title="Detectar automáticamente el banco y tipo de cuenta del contenido del PDF">
              <Button
                variant="outlined"
                startIcon={autoDetecting ? <CircularProgress size={16} /> : <AutoAwesome />}
                onClick={handleAutoDetect}
                disabled={files.length === 0 || autoDetecting}
                size="small"
              >
                {autoDetecting ? 'Detectando...' : 'Auto-Detectar'}
              </Button>
            </Tooltip>
          </Box>

          <Grid container spacing={2}>
            {files.map((file, index) => (
              <Grid item xs={12} key={index}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {file.name}
                  </Typography>
                  
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} md={8}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Banco y Tipo de Cuenta</InputLabel>
                        <Select
                          value={parserSelections[file.name]?.label || ''}
                          label="Banco y Tipo de Cuenta"
                          onChange={(e) => {
                            const parser = parserTypes.find(p => p.label === e.target.value);
                            if (parser) handleParserChange(file.name, parser.id);
                          }}
                        >
                          {parserTypes.map(parser => (
                            <MenuItem key={parser.id} value={parser.label}>
                              {parser.label}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    
                    <Grid item xs={12} md={4}>
                      {parserSelections[file.name] && (
                        <Box>
                          <Chip 
                            label={parserSelections[file.name].label}
                            color={parserSelections[file.name].isAutoSuggested ? "success" : "primary"}
                            size="small"
                            sx={{ mr: 1 }}
                            icon={parserSelections[file.name].isAutoSuggested ? <CheckCircle /> : null}
                          />
                          {parserSelections[file.name].isAutoSuggested && (
                            <Typography variant="caption" color="success.main" sx={{ display: 'block', mt: 0.5 }}>
                              Auto-detectado
                            </Typography>
                          )}
                        </Box>
                      )}
                      {autoSuggestions[file.name]?.error && (
                        <Typography variant="caption" color="error" sx={{ display: 'block', mt: 0.5 }}>
                          {autoSuggestions[file.name].error}
                        </Typography>
                      )}
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Upload Button */}
      {files.length > 0 && (
        <Box sx={{ textAlign: 'center' }}>
          {uploading && <LinearProgress sx={{ mb: 2 }} />}
          <Button
            variant="contained"
            size="large"
            onClick={handleUpload}
            disabled={!canUpload() || uploading}
            sx={{ minWidth: 200 }}
          >
            {uploading ? 'Subiendo...' : sessionId ? 'Iniciar Procesamiento' : `Subir ${files.length} Archivo${files.length > 1 ? 's' : ''}`}
          </Button>
          {sessionId && (
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Archivos subidos exitosamente. Configura los procesadores y haz clic en "Iniciar Procesamiento" para comenzar.
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );
};

export default FileUpload;