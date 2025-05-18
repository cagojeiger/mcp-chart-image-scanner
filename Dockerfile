FROM python:3.10-alpine

# Install Helm CLI and required dependencies
RUN apk add --no-cache curl bash git && \
    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && \
    chmod 700 get_helm.sh && \
    ./get_helm.sh && \
    rm get_helm.sh

# Set working directory
WORKDIR /app

# Copy package files
COPY pyproject.toml README.md ./

# Copy source code
COPY mcp_chart_scanner ./mcp_chart_scanner

# Install the package
RUN pip install --no-cache-dir .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["chart-scanner-server", "--transport", "sse", "--host", "0.0.0.0"]

# Expose default port
EXPOSE 8000
