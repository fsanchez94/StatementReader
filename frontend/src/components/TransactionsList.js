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
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
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
      setError(`Error al cargar transacciones: ${err.message}`);
      setLoading(false);
      console.error('Error loading transactions:', err);
    }
  };

  const handleLoadMore = () => {
    loadTransactions(offset + limit);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-GT', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatAmount = (amount) => {
    return parseFloat(amount).toLocaleString('es-GT', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };

  const getMonthlyDebitData = () => {
    // Filter only debit transactions
    const debits = transactions.filter(t => t.transaction_type.toLowerCase() === 'debit');

    // Group by month
    const monthlyTotals = {};

    debits.forEach(transaction => {
      const date = new Date(transaction.date);
      const monthYear = date.toLocaleDateString('es-GT', {
        month: 'short',
        year: 'numeric'
      });

      if (!monthlyTotals[monthYear]) {
        monthlyTotals[monthYear] = {
          month: monthYear,
          total: 0,
          date: date // Keep for sorting
        };
      }

      monthlyTotals[monthYear].total += parseFloat(transaction.amount);
    });

    // Convert to array and sort by date
    return Object.values(monthlyTotals)
      .sort((a, b) => a.date - b.date)
      .map(({ month, total }) => ({
        month,
        total: parseFloat(total.toFixed(2))
      }));
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

  const monthlyDebitData = getMonthlyDebitData();

  return (
    <Box>
      <Paper elevation={2} sx={{ p: 5, mb: 4, borderRadius: 3 }}>
        <Typography variant="h3" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
          All Transactions
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph sx={{ fontSize: '1.0625rem' }}>
          View all processed transactions from your bank statements.
        </Typography>
      </Paper>

      {/* Monthly Debit Bar Chart */}
      {transactions.length > 0 && monthlyDebitData.length > 0 && (
        <Paper elevation={2} sx={{ p: 4, mb: 4, borderRadius: 3 }}>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 1 }}>
            Monthly Spending
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 3 }}>
            Total debits grouped by month
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={monthlyDebitData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="month"
                angle={-45}
                textAnchor="end"
                height={100}
                style={{ fontSize: '0.875rem' }}
              />
              <YAxis
                style={{ fontSize: '0.875rem' }}
                tickFormatter={(value) =>
                  value.toLocaleString('es-GT', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0
                  })
                }
              />
              <Tooltip
                formatter={(value) =>
                  value.toLocaleString('es-GT', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                  })
                }
                labelStyle={{ fontWeight: 'bold' }}
              />
              <Legend />
              <Bar
                dataKey="total"
                name="Total Debits"
                fill="#FF3B30"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {transactions.length === 0 && !loading ? (
        <Paper elevation={2} sx={{ p: 5, borderRadius: 3 }}>
          <Typography variant="body1" color="text.secondary" align="center" sx={{ fontSize: '1.0625rem' }}>
            No transactions found. Upload and process bank statements to view transactions here.
          </Typography>
        </Paper>
      ) : (
        <>
          <TableContainer component={Paper} elevation={2} sx={{ borderRadius: 3, overflow: 'hidden' }}>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: 'background.default' }}>
                  <TableCell sx={{ color: 'text.primary', fontWeight: 600, py: 2 }}>Date</TableCell>
                  <TableCell sx={{ color: 'text.primary', fontWeight: 600, py: 2 }}>Description</TableCell>
                  <TableCell sx={{ color: 'text.primary', fontWeight: 600, py: 2 }} align="center">Type</TableCell>
                  <TableCell sx={{ color: 'text.primary', fontWeight: 600, py: 2 }} align="right">Amount</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {transactions.map((transaction, index) => (
                  <TableRow
                    key={transaction.id}
                    sx={{
                      '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.02)' },
                      borderBottom: index < transactions.length - 1 ? '1px solid' : 'none',
                      borderColor: 'divider',
                      transition: 'background-color 0.2s ease',
                    }}
                  >
                    <TableCell sx={{ whiteSpace: 'nowrap', py: 2.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {formatDate(transaction.date)}
                      </Typography>
                    </TableCell>
                    <TableCell sx={{ maxWidth: '400px', py: 2.5 }}>
                      <Typography variant="body2">
                        {transaction.description}
                      </Typography>
                    </TableCell>
                    <TableCell align="center" sx={{ py: 2.5 }}>
                      <Chip
                        label={transaction.transaction_type}
                        color={getTransactionTypeColor(transaction.transaction_type)}
                        size="small"
                        sx={{ fontWeight: 600, textTransform: 'capitalize' }}
                      />
                    </TableCell>
                    <TableCell align="right" sx={{ py: 2.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {formatAmount(transaction.amount)}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {hasMore && (
            <Box display="flex" justifyContent="center" mt={4}>
              <Button
                variant="outlined"
                onClick={handleLoadMore}
                disabled={loading}
                sx={{
                  px: 4,
                  py: 1.25,
                }}
              >
                {loading ? <CircularProgress size={22} /> : 'Load More'}
              </Button>
            </Box>
          )}

          <Box mt={3} textAlign="center">
            <Typography variant="body2" color="text.secondary">
              Showing {transactions.length} {transactions.length !== 1 ? 'transactions' : 'transaction'}
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );
}

export default TransactionsList;
