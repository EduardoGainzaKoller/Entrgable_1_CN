const AWS = require('aws-sdk');
const db = new AWS.DynamoDB.DocumentClient();
const TABLE_NAME = process.env.TABLE_NAME;

exports.handler = async (event) => {
  try {
    const { id } = event.pathParameters;

    const result = await db.get({
      TableName: TABLE_NAME,
      Key: { id },
    }).promise();

    if (!result.Item) {
      return { statusCode: 404, body: JSON.stringify({ message: 'Champion not found' }) };
    }

    return { statusCode: 200, body: JSON.stringify(result.Item) };
  } catch (err) {
    console.error(err);
    return { statusCode: 500, body: JSON.stringify({ error: 'Internal server error' }) };
  }
};
