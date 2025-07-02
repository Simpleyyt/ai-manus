# Use Node.js as base image
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/node:18-alpine as build-stage

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json files
COPY package*.json ./

# Install project dependencies
RUN npm ci

# Copy project files
COPY . .

# Build application - skip type checking
RUN npm run build

# Use nginx as production environment image
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/nginx:stable-alpine as production-stage

# Copy built files to nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf.template

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose port 80
EXPOSE 80

# Start nginx with environment variable substitution
CMD ["/docker-entrypoint.sh"] 