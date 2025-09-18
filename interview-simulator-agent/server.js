const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');
const app = express();
const port = process.env.PORT || 8080;

// Backend URL - this should point to your Cloud Run backend
const BACKEND_URL = process.env.BACKEND_URL || '$BACKEND_URL';

// Proxy WebSocket connections to the backend
app.use('/ws', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  ws: true,
  logLevel: 'debug'
}));

// Proxy API calls to the backend
app.use('/api', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  logLevel: 'debug'
}));

// Serve static files from the build directory
app.use(express.static(path.join(__dirname, 'build')));

// Handle React routing, return all requests to React app
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

app.listen(port, () => {
  console.log(`Frontend server is running on port ${port}`);
  console.log(`Backend URL: ${BACKEND_URL}`);
});
