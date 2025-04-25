FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

# Install git
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# pull repo
WORKDIR /app
RUN git clone https://github.com/jagan-shanmugam/open-streetmap-mcp.git
WORKDIR /app/open-streetmap-mcp

RUN pip install -e .

# override src/osm_mcp_server/__init__.py with containers/osm-mcp-extras/__init__.py
COPY containers/osm-mcp-extras/__init__.py /app/open-streetmap-mcp/src/osm_mcp_server/__init__.py

# Expose port 8000 for the server
EXPOSE 8000

# Command to run the server
CMD ["osm-mcp-server"]