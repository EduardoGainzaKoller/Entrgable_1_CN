const AWS = require('aws-sdk');

AWS.config.update({
    region: process.env.AWS_REGION || 'us-east-1',
});

const dynamoDB = new AWS.DynamoDB.DocumentClient();
const TABLE_NAME = process.env.DB_DYNAMONAME || 'Champions';

module.exports = {
    dynamoDB,
    TABLE_NAME
};
