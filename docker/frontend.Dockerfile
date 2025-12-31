FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Default port (override per service)
EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
