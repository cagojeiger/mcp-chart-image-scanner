FROM python:3.12-alpine

# Install Helm and required tools
RUN apk add --no-cache curl bash && \
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash && \
    apk add --no-cache --virtual .build-deps gcc musl-dev && \
    pip install --no-cache-dir uv && \
    apk del .build-deps

WORKDIR /app

# Copy application files
COPY . /app/

# Install dependencies using uv
RUN uv pip install --no-cache-dir -e .

# Expose port for MCP server
EXPOSE 8000

# Run the MCP server
CMD ["python", "-m", "src.mcp_chart_image_scanner.main"]
