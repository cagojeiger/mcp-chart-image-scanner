FROM python:3.12-alpine AS build

# Install build dependencies and Helm
RUN apk add --no-cache curl tar gzip openssl && \
    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && \
    chmod 700 get_helm.sh && \
    ./get_helm.sh

# Install Python dependencies
WORKDIR /app
COPY . .
RUN pip install uv && \
    uv pip install --system -e .

# Final image
FROM python:3.12-alpine

# Install runtime dependencies and Helm
RUN apk add --no-cache curl tar gzip openssl && \
    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && \
    chmod 700 get_helm.sh && \
    ./get_helm.sh

# Copy the installed application
WORKDIR /app
COPY --from=build /app /app
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Set up health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port for SSE transport and health checks
EXPOSE 8000

# Run the MCP server with both transports and health check
ENTRYPOINT ["python", "-m", "src.mcp_chart_image_scanner.main", "--transport", "both", "--host", "0.0.0.0", "--health"]
