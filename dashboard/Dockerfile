# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./

RUN npm install

COPY . .

RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Cài đặt serve để phục vụ static files
RUN npm install -g serve

# Copy build output từ builder stage
COPY --from=builder /app/dist ./dist

# Expose port 5173 (port mặc định Vite) hoặc 3000 (serve)
EXPOSE 3000

# Phục vụ build files
CMD ["serve", "-s", "dist", "-l", "3000"]
