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

# Expose port
EXPOSE ${PORT:-3000}

# Start the application
CMD ["npx", "serve", "-s", "dist", "-l", "${PORT:-3000}"]

