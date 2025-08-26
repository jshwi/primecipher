FROM node:20-alpine

WORKDIR /app

# Install deps
COPY package*.json ./
RUN npm ci

# App source
COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
