import { io } from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
  }

  connect() {
    const socketUrl = process.env.REACT_APP_SOCKET_URL || 'http://localhost:5000';
    this.socket = io(socketUrl, {
      autoConnect: true,
    });

    this.socket.on('connect', () => {
      console.log('Socket connected');
    });

    this.socket.on('disconnect', () => {
      console.log('Socket disconnected');
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  onJobStatus(callback) {
    if (this.socket) {
      this.socket.on('job_status', callback);
    }
  }

  onJobProgress(callback) {
    if (this.socket) {
      this.socket.on('job_progress', callback);
    }
  }

  onJobCompleted(callback) {
    if (this.socket) {
      this.socket.on('job_completed', callback);
    }
  }

  onJobError(callback) {
    if (this.socket) {
      this.socket.on('job_error', callback);
    }
  }

  offAllListeners() {
    if (this.socket) {
      this.socket.removeAllListeners();
    }
  }
}

export const socketService = new SocketService();