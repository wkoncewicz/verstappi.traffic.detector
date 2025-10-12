FROM node:18-alpine AS builder

WORKDIR /app

COPY app/package.json ./
RUN npm install

COPY app/ .

FROM node:18-alpine

WORKDIR /app

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/index.js ./

CMD ["node", "index.js"]