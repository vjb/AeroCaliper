# Use Python 3.11 slim as the base image
FROM python:3.11-slim

# Install Node.js (Required to run the Arize MCP Server via npx)
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency list and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the Arize MCP package globally to ensure it's available
RUN npm install -g @arizeai/phoenix-mcp

# Copy application files
COPY . .

# Expose the Cloud Run port
EXPOSE 8080

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
