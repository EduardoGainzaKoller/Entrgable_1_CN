FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm ci --only=production

COPY . .

EXPOSE 8080

ENV PORT=8080
ENV AWS_REGION=us-east-1
ENV DYNAMODB_TABLE=Champions

CMD [ "node", "server.js" ]