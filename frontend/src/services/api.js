import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      timeout: 300000, // 5 minutes for file processing
    });
  }

  async getParserTypes() {
    const response = await this.client.get('/parser-types/');
    return response.data;
  }

  async uploadFiles(files, parserSelections, accountHolders) {
    const formData = new FormData();
    
    files.forEach(file => {
      formData.append('files', file);
    });
    
    if (parserSelections) {
      formData.append('parsers', JSON.stringify(parserSelections));
    }
    
    if (accountHolders) {
      formData.append('account_holders', JSON.stringify(accountHolders));
    }
    
    const response = await this.client.post('/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  }

  async processSession(sessionId) {
    const response = await this.client.post(`/process/${sessionId}/`);
    return response.data;
  }

  async getSessionStatus(sessionId) {
    const response = await this.client.get(`/status/${sessionId}/`);
    return response.data;
  }

  async downloadFile(sessionId) {
    const response = await this.client.get(`/download/${sessionId}/`, {
      responseType: 'blob',
    });
    
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'transactions.csv';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }
    
    this._createDownloadLink(response.data, filename);
  }

  async cleanupSession(sessionId) {
    await this.client.delete(`/cleanup/${sessionId}/`);
  }

  _createDownloadLink(data, filename) {
    // Create download link
    const url = window.URL.createObjectURL(new Blob([data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
}

export const apiService = new ApiService();