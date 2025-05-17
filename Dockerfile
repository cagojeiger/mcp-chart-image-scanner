FROM python:3.12-slim

# Install Helm
RUN apt-get update && \
    apt-get install -y curl && \
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application files
COPY extract_docker_images.py mcp_server.py main.py requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for MCP server
EXPOSE 8000

# Run the MCP server
CMD ["python", "main.py"]
