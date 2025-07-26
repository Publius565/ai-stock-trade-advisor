# Docker Setup for AI-Driven Stock Trade Advisor

This directory contains Docker configuration files for containerizing the AI-Driven Stock Trade Advisor application.

## Files Overview

- **Dockerfile**: Multi-stage build configuration for production and development
- **docker-compose.yml**: Orchestration file for running services
- **.dockerignore**: Excludes unnecessary files from build context
- **README.md**: This documentation file

## Prerequisites

1. **Docker**: Install Docker Desktop or Docker Engine
   - Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Linux: [Docker Engine](https://docs.docker.com/engine/install/)
   - macOS: [Docker Desktop](https://www.docker.com/products/docker-desktop)

2. **Docker Compose**: Usually included with Docker Desktop
   - Verify installation: `docker-compose --version`

3. **API Keys**: Configure your API keys in `config/api_keys.env`

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and run the application**:
   ```bash
   # Production mode
   docker-compose -f docker/docker-compose.yml up -d
   
   # Development mode
   docker-compose -f docker/docker/docker-compose.yml --profile dev up -d
   ```

2. **Access the application**:
   - Production: http://localhost:8080
   - Development: http://localhost:8081

3. **Stop the application**:
   ```bash
   docker-compose -f docker/docker-compose.yml down
   ```

### Using Docker Management Script

1. **Check Docker installation**:
   ```bash
   python scripts/docker_management.py check
   ```

2. **Build the image**:
   ```bash
   python scripts/docker_management.py build
   ```

3. **Run the container**:
   ```bash
   python scripts/docker_management.py run
   ```

4. **View logs**:
   ```bash
   python scripts/docker_management.py logs
   ```

5. **Stop the container**:
   ```bash
   python scripts/docker_management.py stop
   ```

## Docker Configuration

### Multi-Stage Build

The Dockerfile uses a multi-stage build approach:

1. **Builder Stage**: Installs dependencies and creates virtual environment
2. **Production Stage**: Creates lightweight production image

### Security Features

- **Non-root user**: Application runs as `trading_advisor` user
- **Read-only mounts**: API keys mounted as read-only
- **Resource limits**: Memory and CPU limits in production
- **Health checks**: Container health monitoring

### Volume Mounts

The following directories are mounted as volumes for data persistence:

- `data/`: Database and market data
- `models/`: Machine learning models
- `logs/`: Application logs
- `config/`: Configuration files

### Environment Variables

Key environment variables:

- `DEBUG_MODE`: Enable/disable debug mode
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `DATABASE_PATH`: Path to SQLite database
- `LOG_FILE`: Path to log file

## Development vs Production

### Development Mode

- Debug logging enabled
- Source code mounted for live editing
- Additional development tools included
- Runs on port 8081

### Production Mode

- Optimized for performance
- Minimal logging
- Resource limits applied
- Runs on port 8080

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Check what's using the port
   netstat -ano | findstr :8080
   
   # Use a different port
   python scripts/docker_management.py run --port 8082
   ```

2. **Permission denied**:
   ```bash
   # Ensure Docker has proper permissions
   # On Linux, add user to docker group
   sudo usermod -aG docker $USER
   ```

3. **API keys not found**:
   ```bash
   # Ensure api_keys.env exists
   cp config/api_keys.env.example config/api_keys.env
   # Edit with your actual API keys
   ```

4. **Container won't start**:
   ```bash
   # Check container logs
   python scripts/docker_management.py logs
   
   # Check container status
   python scripts/docker_management.py status
   ```

### Debugging

1. **Run in interactive mode**:
   ```bash
   docker run -it --rm ai-trading-advisor:latest /bin/bash
   ```

2. **Check container health**:
   ```bash
   docker ps --filter name=ai-trading-advisor
   ```

3. **Inspect container**:
   ```bash
   docker inspect ai-trading-advisor
   ```

## Performance Optimization

### Resource Limits

Production containers have resource limits:
- Memory: 2GB
- CPU: 1 core

### Build Optimization

- Multi-stage build reduces image size
- .dockerignore excludes unnecessary files
- Layer caching for faster rebuilds

### Volume Optimization

- Use named volumes for better performance
- Avoid mounting large directories unnecessarily

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Network**: Use internal Docker networks
3. **User**: Application runs as non-root user
4. **Updates**: Regularly update base images

## Monitoring

### Health Checks

The container includes health checks:
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 40 seconds

### Logging

- Application logs: `/app/logs/trading_advisor.log`
- Container logs: `docker logs ai-trading-advisor`
- Follow logs: `docker logs -f ai-trading-advisor`

## Backup and Recovery

### Data Backup

```bash
# Backup data directory
docker cp ai-trading-advisor:/app/data ./backup/data

# Backup models directory
docker cp ai-trading-advisor:/app/models ./backup/models
```

### Restore Data

```bash
# Restore data directory
docker cp ./backup/data ai-trading-advisor:/app/data

# Restart container
docker restart ai-trading-advisor
```

## Advanced Usage

### Custom Build

```bash
# Build with custom tag
docker build -f docker/Dockerfile -t my-trading-advisor:v1.0 .

# Build with build arguments
docker build -f docker/Dockerfile --build-arg PYTHON_VERSION=3.11 .
```

### Custom Compose

```bash
# Use custom compose file
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml up

# Override environment variables
docker-compose -f docker/docker-compose.yml up -e DEBUG_MODE=true
```

### Scaling

```bash
# Scale services (if multiple instances needed)
docker-compose -f docker/docker-compose.yml up --scale trading-advisor=3
```

## Support

For Docker-related issues:

1. Check the troubleshooting section above
2. Review container logs
3. Verify Docker installation
4. Check file permissions and paths

## Version History

- **v1.0**: Initial Docker setup with multi-stage build
- **v1.1**: Added Docker Compose configuration
- **v1.2**: Added management scripts and documentation 