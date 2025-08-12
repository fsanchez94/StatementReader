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
  LinearProgress
} from '@mui/material';
import {
  CloudUpload,
  Delete,
  PictureAsPdf,
  Assignment
} from '@mui/icons-material';
import { apiService } from '../services/api';

const FileUpload = ({ parserTypes, onFilesUploaded }) => {
  const [files, setFiles] = useState([]);
  const [parserSelections, setParserSelections] = useState({});
  const [accountHolders, setAccountHolders] = useState({});
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const pdfFiles = acceptedFiles.filter(file => 
      file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
    );
    
    if (pdfFiles.length !== acceptedFiles.length) {
      setError('Only PDF files are accepted');
      return;
    }

    setFiles(prev => [...prev, ...pdfFiles]);
    setError(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
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
    
    // Remove account holder selection for this file
    setAccountHolders(prev => {
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
        label: parser.label
      }
    }));
  };

  const handleAccountHolderChange = (filename, holder) => {
    setAccountHolders(prev => ({
      ...prev,
      [filename]: holder
    }));
  };

  const canUpload = () => {
    if (files.length === 0) return false;
    
    // Check that all files have parser and account holder selections
    return files.every(file => 
      parserSelections[file.name] && accountHolders[file.name]
    );
  };

  const handleUpload = async () => {
    if (!canUpload()) {
      setError('Please select parser and account holder for all files');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const result = await apiService.uploadFiles(files, parserSelections, accountHolders);
      onFilesUploaded(result.session_id);
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
          {isDragActive ? 'Drop PDF files here' : 'Drag & drop PDF files here'}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          or click to browse files
        </Typography>
        <Button variant="outlined" sx={{ mt: 2 }}>
          Browse Files
        </Button>
      </Paper>

      {/* File List */}
      {files.length > 0 && (
        <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Selected Files ({files.length})
          </Typography>
          
          <List>
            {files.map((file, index) => (
              <ListItem key={index} divider>
                <PictureAsPdf sx={{ mr: 2, color: 'error.main' }} />
                <ListItemText
                  primary={file.name}
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
            ))}
          </List>
        </Paper>
      )}

      {/* Parser Selection */}
      {files.length > 0 && (
        <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            <Assignment sx={{ mr: 1, verticalAlign: 'middle' }} />
            Configure Parsers
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Select the appropriate bank and account type for each file
          </Typography>

          <Grid container spacing={2}>
            {files.map((file, index) => (
              <Grid item xs={12} key={index}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {file.name}
                  </Typography>
                  
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} md={5}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Bank & Account Type</InputLabel>
                        <Select
                          value={parserSelections[file.name]?.label || ''}
                          label="Bank & Account Type"
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
                    
                    <Grid item xs={12} md={3}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Account Holder</InputLabel>
                        <Select
                          value={accountHolders[file.name] || ''}
                          label="Account Holder"
                          onChange={(e) => handleAccountHolderChange(file.name, e.target.value)}
                        >
                          <MenuItem value="husband">Husband</MenuItem>
                          <MenuItem value="spouse">Spouse</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    
                    <Grid item xs={12} md={4}>
                      {parserSelections[file.name] && accountHolders[file.name] && (
                        <Box>
                          <Chip 
                            label={parserSelections[file.name].label}
                            color="primary"
                            size="small"
                            sx={{ mr: 1 }}
                          />
                          <Chip 
                            label={accountHolders[file.name]}
                            color="secondary"
                            size="small"
                          />
                        </Box>
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
            {uploading ? 'Uploading...' : `Process ${files.length} File${files.length > 1 ? 's' : ''}`}
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default FileUpload;