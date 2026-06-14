# Use a lightweight Node.js image
FROM node:22-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package files first (to optimize caching)
COPY package*.json ./

# Install frontend dependencies
RUN npm install

# Copy the rest of your React code
COPY . .

# Expose the port your frontend runs on (Vite uses 5173, Create React App uses 3000)
EXPOSE 5173

# Command to start the React development server
CMD ["npm", "run", "dev"] 
# (Note: If you used Create React App instead of Vite, change this to CMD ["npm", "start"])