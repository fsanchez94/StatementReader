import React from 'react';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  CircularProgress
} from '@mui/material';
import {
  Schedule,
  PlayArrow,
  CheckCircle,
  PictureAsPdf
} from '@mui/icons-material';

const ProcessingStatus = ({ job }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'processing':
        return <CircularProgress size={20} />;
      case 'completed':
        return <CheckCircle color="success" />;
      default:
        return <Schedule color="warning" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'uploaded':
        return 'Files uploaded, starting processing...';
      case 'processing':
        return 'Processing files...';
      case 'completed':
        return 'Processing completed!';
      default:
        return 'Unknown status';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'processing':
        return 'info';
      case 'completed':
        return 'success';
      default:
        return 'warning';
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        {getStatusIcon(job?.status)}
        <Box sx={{ ml: 2, flexGrow: 1 }}>
          <Typography variant="h5">
            Processing Bank Statements
          </Typography>
          <Typography variant="body1" color="textSecondary">
            {getStatusText(job?.status)}
          </Typography>
        </Box>
        <Chip 
          label={job?.status || 'unknown'} 
          color={getStatusColor(job?.status)}
          variant="outlined"
        />
      </Box>

      {/* Progress Bar */}
      {job?.progress !== undefined && (
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">
              Progress
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {job.progress}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={job.progress || 0} 
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>
      )}

      {/* Current File */}
      {job?.currentFile && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="primary" gutterBottom>
            Currently Processing:
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <PictureAsPdf sx={{ mr: 1, color: 'error.main' }} />
            <Typography variant="body2">
              {job.currentFile}
            </Typography>
          </Box>
        </Box>
      )}

      {/* File Status List */}
      {job?.files && job.files.length > 0 && (
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Files to Process ({job.files.length}):
          </Typography>
          <List dense>
            {job.files.map((file, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <PictureAsPdf fontSize="small" color="error" />
                </ListItemIcon>
                <ListItemText
                  primary={file.filename}
                  secondary={`${file.parser?.label || 'Parser not set'} • ${file.account_holder || 'Unknown holder'}`}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {/* Processing Stats */}
      {job?.totalFiles && (
        <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="body2" color="textSecondary">
            Processing {job.processedFiles || 0} of {job.totalFiles} files
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default ProcessingStatus;