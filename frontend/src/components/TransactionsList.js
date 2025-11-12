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
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Todas las Transacciones
        </Typography>
        <Typography variant="body1" color="textSecondary" paragraph>
          Ver todas las transacciones procesadas de tus estados de cuenta.
        </Typography>
      </Paper>

      {/* Monthly Debit Bar Chart */}
      {transactions.length > 0 && monthlyDebitData.length > 0 && (
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Gastos Mensuales (Débitos)
          </Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            Suma total de débitos agrupados por mes
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
                name="Total Débitos"
                fill="#d32f2f"
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
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="body1" color="textSecondary" align="center">
            No se encontraron transacciones. Sube y procesa estados de cuenta para ver transacciones aquí.
          </Typography>
        </Paper>
      ) : (
        <>
          <TableContainer component={Paper} elevation={3}>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: 'primary.main' }}>
                  <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Fecha</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Descripción</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="center">Tipo</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 'bold' }} align="right">Monto</TableCell>
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
                {loading ? <CircularProgress size={24} /> : 'Cargar Más'}
              </Button>
            </Box>
          )}

          <Box mt={2} textAlign="center">
            <Typography variant="body2" color="textSecondary">
              Mostrando {transactions.length} {transactions.length !== 1 ? 'transacciones' : 'transacción'}
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );
}

export default TransactionsList;
