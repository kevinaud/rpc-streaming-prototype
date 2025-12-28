FROM node:22-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source (for initial build; volume mount overrides in dev)
COPY . .

EXPOSE 4200
