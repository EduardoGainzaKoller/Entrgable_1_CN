const express = require('express');
const cors = require('cors');
const path = require('path');
const championRoutes = require('./src/routes/championRoutes');

const app = express();
const PORT = process.env.PORT || 8080;

// ---------------------------
// Middlewares
// ---------------------------
app.use(cors());
app.use(express.json());

// Logger simple
app.use((req, res, next) => {
    console.log(`${req.method} ${req.url}`);
    next();
});

// ---------------------------
// Endpoint Health
// ---------------------------
app.get('/health', (req, res) => {
    res.json({ status: 'OK' });
});

// ---------------------------
// API Routes
// ---------------------------
app.use('/api', championRoutes);


app.use(express.static(path.join(__dirname, 'public')));


app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.use((req, res) => {
    res.status(404).json({ error: 'Not Found' });
});

app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Internal Server Error' });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server is running on port ${PORT}`);
});
