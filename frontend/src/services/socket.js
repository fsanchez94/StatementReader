class SocketService {
  constructor() {
    this.socket = null;
    this.sessionId = null;
  }

  connect(sessionId) {
    this.sessionId = sessionId;
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:5000';
    this.socket = new WebSocket(`${wsUrl}/ws/progress/${sessionId}/`);

    this.socket.onopen = () => {
      console.log('WebSocket connected');
    };

    this.socket.onclose = () => {
      console.log('WebSocket disconnected');
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  onMessage(callback) {
    if (this.socket) {
      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        callback(data);
      };
    }
  }
}

export const socketService = new SocketService();