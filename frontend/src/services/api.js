import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      timeout: 300000, // 5 minutes for file processing
    });
  }

  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }

  async getParserTypes() {
    const response = await this.client.get('/parser-types');
    return response.data;
  }

  async uploadFiles(files, parserSelections, accountHolders) {
    const formData = new FormData();
    
    // Add files
    files.forEach(file => {
      formData.append('files', file);
    });
    
    // Add parser selections
    formData.append('parsers', JSON.stringify(parserSelections));
    
    // Add account holders
    formData.append('account_holders', JSON.stringify(accountHolders));
    
    const response = await this.client.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  }

  async processJob(jobId) {
    const response = await this.client.post(`/process/${jobId}`);
    return response.data;
  }

  async getJobStatus(jobId) {
    const response = await this.client.get(`/job/${jobId}`);
    return response.data;
  }

  async getAvailableFiles() {
    const response = await this.client.get('/debug/files');
    return response.data;
  }

  getDownloadUrl(jobId, filename) {
    return `${API_BASE}/download/${jobId}/${filename}`;
  }

  getDirectDownloadUrl(filename) {
    return `${API_BASE}/download-direct/${filename}`;
  }

  async downloadFile(jobId, filename) {
    try {
      // Try the original job-based download first
      const response = await this.client.get(`/download/${jobId}/${filename}`, {
        responseType: 'blob',
      });
      
      this._createDownloadLink(response.data, filename);
    } catch (error) {
      // If job-based download fails, try direct download
      console.log('Job-based download failed, trying direct download...');
      await this.downloadFileDirect(filename);
    }
  }

  async downloadFileDirect(filename) {
    const response = await this.client.get(`/download-direct/${filename}`, {
      responseType: 'blob',
    });
    
    this._createDownloadLink(response.data, filename);
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