FROM node:20-alpine

WORKDIR /app

# Install deps first for better caching. Code is bind-mounted at runtime.
COPY package.json package-lock.json ./
RUN npm ci

# Source is bind-mounted via docker-compose; this COPY is just a safe baseline.
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1 \
    WATCHPACK_POLLING=true \
    CHOKIDAR_USEPOLLING=true

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
