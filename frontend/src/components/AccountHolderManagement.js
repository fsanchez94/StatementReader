import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Box,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Star as StarIcon
} from '@mui/icons-material';
import { apiService } from '../services/api';

const PRESET_COLORS = [
  '#3498db', // Blue
  '#e74c3c', // Red
  '#2ecc71', // Green
  '#f39c12', // Orange
  '#9b59b6', // Purple
  '#1abc9c', // Turquoise
  '#34495e', // Dark Gray
  '#e67e22', // Carrot
];

export default function AccountHolderManagement() {
  const [holders, setHolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingHolder, setEditingHolder] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    color: PRESET_COLORS[0],
    is_default: false
  });

  useEffect(() => {
    loadHolders();
  }, []);

  const loadHolders = async () => {
    try {
      setLoading(true);
      const data = await apiService.getAccountHolders();
      setHolders(data.account_holders || []);
      setError('');
    } catch (err) {
      setError('Error loading account holders: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (holder = null) => {
    if (holder) {
      setEditingHolder(holder);
      setFormData({
        name: holder.name,
        color: holder.color,
        is_default: holder.is_default
      });
    } else {
      setEditingHolder(null);
      setFormData({
        name: '',
        color: PRESET_COLORS[0],
        is_default: false
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingHolder(null);
    setFormData({
      name: '',
      color: PRESET_COLORS[0],
      is_default: false
    });
  };

  const handleSubmit = async () => {
    try {
      if (!formData.name.trim()) {
        setError('Name is required');
        return;
      }

      if (editingHolder) {
        await apiService.updateAccountHolder(editingHolder.id, formData);
        setSuccess('Account holder updated successfully');
      } else {
        await apiService.createAccountHolder(formData);
        setSuccess('Account holder created successfully');
      }

      handleCloseDialog();
      loadHolders();

      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Error saving account holder: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleDelete = async (holder) => {
    if (!window.confirm(`Are you sure you want to delete "${holder.name}"? This will unassign all files and transactions from this account holder.`)) {
      return;
    }

    try {
      await apiService.deleteAccountHolder(holder.id);
      setSuccess('Account holder deleted successfully');
      loadHolders();

      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Error deleting account holder: ' + (err.response?.data?.error || err.message));
    }
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4">Account Holders</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add Account Holder
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
            {success}
          </Alert>
        )}

        {holders.length === 0 ? (
          <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
            No account holders yet. Click "Add Account Holder" to create one.
          </Typography>
        ) : (
          <List>
            {holders.map((holder) => (
              <ListItem
                key={holder.id}
                secondaryAction={
                  <Box>
                    <IconButton
                      edge="end"
                      aria-label="edit"
                      onClick={() => handleOpenDialog(holder)}
                      sx={{ mr: 1 }}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      edge="end"
                      aria-label="delete"
                      onClick={() => handleDelete(holder)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                }
                sx={{
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  mb: 1
                }}
              >
                <Box sx={{ mr: 2 }}>
                  <Chip
                    label=""
                    sx={{
                      backgroundColor: holder.color,
                      width: 40,
                      height: 40
                    }}
                  />
                </Box>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="h6">{holder.name}</Typography>
                      {holder.is_default && (
                        <Chip
                          icon={<StarIcon />}
                          label="Default"
                          size="small"
                          color="primary"
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <Typography variant="body2" color="text.secondary">
                      Color: {holder.color}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </Paper>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingHolder ? 'Edit Account Holder' : 'Add Account Holder'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Name"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2, mt: 1 }}
          />

          <Typography variant="subtitle2" gutterBottom>
            Color
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            {PRESET_COLORS.map((color) => (
              <Box
                key={color}
                onClick={() => setFormData({ ...formData, color })}
                sx={{
                  width: 40,
                  height: 40,
                  backgroundColor: color,
                  border: formData.color === color ? '3px solid #000' : '1px solid #ccc',
                  borderRadius: '50%',
                  cursor: 'pointer',
                  '&:hover': {
                    opacity: 0.8
                  }
                }}
              />
            ))}
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <input
              type="checkbox"
              id="is_default"
              checked={formData.is_default}
              onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
            />
            <label htmlFor="is_default">
              <Typography variant="body2">
                Set as default account holder
              </Typography>
            </label>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingHolder ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
