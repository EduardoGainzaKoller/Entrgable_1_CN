// src/controllers/ChampionController.js
const Champion = require('../models/Champion');
const { dynamoDB, TABLE_NAME } = require('../config/dynamoDB');

exports.createChampion = async (req, res) => {
    try {
        const champion = new Champion(req.body);

        // Validates champion data
        champion.validate();

        // Prepares the DynamoDB put parameters
        const params = {
            TableName: TABLE_NAME,
            Item: champion.toJSON()
        };

        await dynamoDB.put(params).promise();

        res.status(201).json(champion.toJSON());
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
};

exports.getAllChampions = async (req, res) => {
    try {
        const params = {
            TableName: TABLE_NAME
        }; 

        const data = await dynamoDB.scan(params).promise();

        res.json(data.Items);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.getChampionById = async (req, res) => {
    try {
        const params = {
            TableName: TABLE_NAME,
            Key: { id: req.params.id }
        }

        const data = await dynamoDB.get(params).promise();

        if (!data.Item) {
            return res.status(404).json({ error: 'Champion not found' });
        }

        res.json(data.Item);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

exports.updateChampion = async (req, res) => {
    try {
        const params = {
            TableName: TABLE_NAME,
            Key: { id: req.params.id }
        };

        const existingChampion = await dynamoDB.get(params).promise();

        if (!existingChampion.Item) {
            return res.status(404).json({ error: 'Champion not found' });
        }

        const update = req.body;
        update.updatedAt = new Date().toISOString();

        let updateExpression = 'SET';
        const expressionAttributeNames = {};
        const expressionAttributeValues = {};

        Object.keys(update).forEach((key, index) => {
            if (key !== 'id') {
                const placeholder = `#key${index}`;
                const valuePlaceholder = `:value${index}`;
                updateExpression += ` ${placeholder} = ${valuePlaceholder},`;
                expressionAttributeNames[placeholder] = key;
                expressionAttributeValues[valuePlaceholder] = update[key];
            }
        });

        updateExpression = updateExpression.slice(0, -1); // Remove trailing comma

        const updateParams = {
            TableName: TABLE_NAME,
            Key: { id: req.params.id },
            UpdateExpression: updateExpression,
            ExpressionAttributeNames: expressionAttributeNames,
            ExpressionAttributeValues: expressionAttributeValues,
            ReturnValues: 'ALL_NEW'
        };
        const result = await dynamoDB.update(updateParams).promise();

        res.json(result.Attributes);
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
};

exports.deleteChampion = async (req, res) => {
    try {
        // If not exists
        const getParams = {
            TableName: TABLE_NAME,
            Key: { id: req.params.id }
        };
        const existingChampion = await dynamoDB.get(getParams).promise();

        if (!existingChampion.Item) {
            return res.status(404).json({ error: 'Champion not found' });
        }

        // if exists, delete
        const params = {
            TableName: TABLE_NAME,
            Key: { id: req.params.id }
        };
        await dynamoDB.delete(params).promise();

        res.status(204).send();
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};