// src/models/Champion.js

const { v4: uuidv4 } = require('uuid');

class Champion {
    constructor(data) {
        this.id = uuidv4();
        this.name = data.name;
        this.role = data.role;
        this.difficulty = data.difficulty;
        this.abilities = data.abilities; // abilities is expected to be an array of strings
        this.createdAt = new Date().toISOString();
        this.updatedAt = new Date().toISOString();
    }

    validate() {
        if (!this.name || typeof this.name !== 'string') {
            throw new Error('Invalid or missing name');
        }
        if (!this.role || typeof this.role !== 'string') {
            throw new Error('Invalid or missing role');
        }
        if (!this.difficulty || typeof this.difficulty !== 'string') {
            throw new Error('Invalid or missing difficulty');
        }
        if (!Array.isArray(this.abilities) || this.abilities.some(ability => typeof ability !== 'string')) {
            throw new Error('Invalid or missing abilities');
        }
    }

    toJSON() {
        return {
            id: this.id,
            name: this.name,
            role: this.role,
            difficulty: this.difficulty,
            abilities: this.abilities,
            createdAt: this.createdAt,
            updatedAt: this.updatedAt
        };
    }
}

module.exports = Champion;