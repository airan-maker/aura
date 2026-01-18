# Frontend Dockerfile for Next.js (Development)

FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json ./
RUN npm install

# Copy source files
COPY . .

EXPOSE 3000

# Development server
CMD ["npm", "run", "dev"]
