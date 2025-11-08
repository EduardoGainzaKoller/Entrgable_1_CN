// src/routes/championRoutes.js
const express = require('express');
const ChampionController = require('../controllers/ChampionController');
const router = express.Router();

router.post('/champions', ChampionController.createChampion);
router.get('/champions', ChampionController.getAllChampions);
router.get('/champions/:id', ChampionController.getChampionById);
router.put('/champions/:id', ChampionController.updateChampion);
router.delete('/champions/:id', ChampionController.deleteChampion);

module.exports = router;