import React, { useState, useEffect } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Button,
  Chip
} from '@mui/material';
import { apiService } from '../services/api';

function TransactionsList() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);
  const limit = 50;

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async (newOffset = 0) => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiService.getTransactions({
        limit,
        offset: newOffset
      });

      if (newOffset === 0) {
        setTransactions(response.transactions);
      } else {
        setTransactions(prev => [...prev, ...response.transactions]);
      }

      setHasMore(response.has_more);
      setOffset(newOffset);
      setLoading(false);
    } catch (err) {
      setError(`Failed to load transactions: ${err.message}`);
      setLoading(false);
      console.error('Error loading transactions:', err);
    }
  };

  const handleLoadMore = () => {
    loadTransactions(offset + limit);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatAmount = (amount) => {
    return parseFloat(amount).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };

  const getTransactionTypeColor = (type) => {
    return type.toLowerCase() === 'credit' ? 'success' : 'error';
  };

  if (loading && transactions.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          All Transactions
        </Typography>
        <Typography variant="body1" color="textSecondary" paragraph>
          View all processed transactions from your bank statements.
        </Typography>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {transactions.length === 0 && !loading ? (
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="body1" color="textSecondary" align="center">
            No transactions found. Upload and process some bank statements to see transactions here.
          </Typography>
        </Paper>
      ) : (
        <>
          <TableContainer component={Paper} elevation={3}>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: 'primary.main' }}>
                  <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Date</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Description</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="center">Type</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">Amount</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {transactions.map((transaction) => (
                  <TableRow
                    key={transaction.id}
                    hover
                    sx={{ '&:hover': { backgroundColor: 'action.hover' } }}
                  >
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>
                      {formatDate(transaction.date)}
                    </TableCell>
                    <TableCell sx={{ maxWidth: '400px' }}>
                      {transaction.description}
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={transaction.transaction_type.toUpperCase()}
                        color={getTransactionTypeColor(transaction.transaction_type)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'medium' }}>
                      {formatAmount(transaction.amount)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {hasMore && (
            <Box display="flex" justifyContent="center" mt={3}>
              <Button
                variant="outlined"
                onClick={handleLoadMore}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Load More'}
              </Button>
            </Box>
          )}

          <Box mt={2} textAlign="center">
            <Typography variant="body2" color="textSecondary">
              Showing {transactions.length} transaction{transactions.length !== 1 ? 's' : ''}
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );
}

export default TransactionsList;
