# frontend/Dockerfile

# Stage 1: Build the React application
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Set the API URL during the build
# Although we are using a proxy, it's good practice
# to set it for consistency if needed elsewhere.
ARG VITE_API_URL=/api
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:1.21.0-alpine

# Copy the built files from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Remove the default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
