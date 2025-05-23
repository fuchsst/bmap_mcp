FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r bmad && useradd -r -g bmad bmad

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Change ownership to non-root user
RUN chown -R bmad:bmad /app

# Switch to non-root user
USER bmad

# Expose port for SSE mode
EXPOSE 8000

# Default command (stdio mode)
CMD ["python", "-m", "bmad_mcp_server.main", "--mode", "stdio"]
