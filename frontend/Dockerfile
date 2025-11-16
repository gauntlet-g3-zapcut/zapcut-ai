FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Expose port (Railway will set PORT env var)
EXPOSE 3000

# Start the application (Railway will override with startCommand)
CMD ["npx", "serve", "-s", "dist", "-l", "3000"]

