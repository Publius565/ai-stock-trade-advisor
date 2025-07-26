#!/usr/bin/env python3
"""
Docker Management Script

This script provides utilities for building, running, and managing Docker containers
for the AI-Driven Stock Trade Advisor application.
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

def run_command(command, check=True, capture_output=False):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        return None

def check_docker_installed():
    """Check if Docker is installed and running."""
    result = run_command("docker --version", check=False, capture_output=True)
    if result and result.returncode == 0:
        print(f"Docker version: {result.stdout.strip()}")
        return True
    else:
        print("Docker is not installed or not accessible")
        return False

def check_docker_compose_installed():
    """Check if Docker Compose is installed."""
    result = run_command("docker-compose --version", check=False, capture_output=True)
    if result and result.returncode == 0:
        print(f"Docker Compose version: {result.stdout.strip()}")
        return True
    else:
        print("Docker Compose is not installed or not accessible")
        return False

def build_image(tag="ai-trading-advisor:latest"):
    """Build the Docker image."""
    print(f"Building Docker image: {tag}")
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    dockerfile_path = project_root / "docker" / "Dockerfile"
    
    if not dockerfile_path.exists():
        print(f"Error: Dockerfile not found at {dockerfile_path}")
        return False
    
    command = f"docker build -f {dockerfile_path} -t {tag} {project_root}"
    result = run_command(command)
    
    if result and result.returncode == 0:
        print(f"Successfully built image: {tag}")
        return True
    else:
        print("Failed to build Docker image")
        return False

def run_container(tag="ai-trading-advisor:latest", port=8080, detach=True):
    """Run the Docker container."""
    print(f"Running container from image: {tag}")
    
    # Create necessary directories
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    models_dir = project_root / "models"
    logs_dir = project_root / "logs"
    config_dir = project_root / "config"
    
    for directory in [data_dir, models_dir, logs_dir, config_dir]:
        directory.mkdir(exist_ok=True)
    
    # Build docker run command
    detach_flag = "-d" if detach else ""
    command = f"""docker run {detach_flag} \
        --name ai-trading-advisor \
        -p {port}:8080 \
        -v {data_dir.absolute()}:/app/data \
        -v {models_dir.absolute()}:/app/models \
        -v {logs_dir.absolute()}:/app/logs \
        -v {config_dir.absolute()}:/app/config \
        --env-file {config_dir.absolute()}/api_keys.env \
        {tag}"""
    
    result = run_command(command)
    
    if result and result.returncode == 0:
        print(f"Container started successfully on port {port}")
        if detach:
            print("Container is running in detached mode")
        return True
    else:
        print("Failed to start container")
        return False

def stop_container():
    """Stop the running container."""
    print("Stopping container...")
    command = "docker stop ai-trading-advisor"
    result = run_command(command)
    
    if result and result.returncode == 0:
        print("Container stopped successfully")
        return True
    else:
        print("Failed to stop container or container not running")
        return False

def remove_container():
    """Remove the container."""
    print("Removing container...")
    command = "docker rm ai-trading-advisor"
    result = run_command(command)
    
    if result and result.returncode == 0:
        print("Container removed successfully")
        return True
    else:
        print("Failed to remove container or container not found")
        return False

def run_with_compose(profile="production"):
    """Run the application using Docker Compose."""
    print(f"Running with Docker Compose (profile: {profile})")
    
    project_root = Path(__file__).parent.parent
    compose_file = project_root / "docker" / "docker-compose.yml"
    
    if not compose_file.exists():
        print(f"Error: docker-compose.yml not found at {compose_file}")
        return False
    
    # Change to project root directory
    os.chdir(project_root)
    
    if profile == "dev":
        command = "docker-compose -f docker/docker-compose.yml --profile dev up -d"
    else:
        command = "docker-compose -f docker/docker-compose.yml up -d"
    
    result = run_command(command)
    
    if result and result.returncode == 0:
        print("Docker Compose services started successfully")
        return True
    else:
        print("Failed to start Docker Compose services")
        return False

def stop_compose():
    """Stop Docker Compose services."""
    print("Stopping Docker Compose services...")
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    command = "docker-compose -f docker/docker-compose.yml down"
    result = run_command(command)
    
    if result and result.returncode == 0:
        print("Docker Compose services stopped successfully")
        return True
    else:
        print("Failed to stop Docker Compose services")
        return False

def show_logs(container_name="ai-trading-advisor", follow=False):
    """Show container logs."""
    follow_flag = "-f" if follow else ""
    command = f"docker logs {follow_flag} {container_name}"
    result = run_command(command, check=False)
    
    if result:
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    else:
        print("Failed to retrieve logs")

def show_status():
    """Show container and image status."""
    print("=== Docker Images ===")
    run_command("docker images ai-trading-advisor", check=False)
    
    print("\n=== Running Containers ===")
    run_command("docker ps -a --filter name=ai-trading-advisor", check=False)
    
    print("\n=== Docker Compose Services ===")
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    run_command("docker-compose -f docker/docker-compose.yml ps", check=False)

def clean_up():
    """Clean up Docker resources."""
    print("Cleaning up Docker resources...")
    
    # Stop and remove containers
    stop_container()
    remove_container()
    
    # Remove images
    command = "docker rmi ai-trading-advisor:latest"
    run_command(command, check=False)
    
    print("Cleanup completed")

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Docker management for AI Trading Advisor")
    parser.add_argument("action", choices=[
        "check", "build", "run", "stop", "remove", "compose", "stop-compose",
        "logs", "status", "cleanup"
    ], help="Action to perform")
    parser.add_argument("--tag", default="ai-trading-advisor:latest", help="Docker image tag")
    parser.add_argument("--port", type=int, default=8080, help="Port to expose")
    parser.add_argument("--profile", choices=["production", "dev"], default="production", 
                       help="Docker Compose profile")
    parser.add_argument("--follow", action="store_true", help="Follow logs")
    
    args = parser.parse_args()
    
    # Check Docker installation first
    if not check_docker_installed():
        print("Docker is required but not installed")
        sys.exit(1)
    
    # Perform requested action
    if args.action == "check":
        check_docker_compose_installed()
    elif args.action == "build":
        build_image(args.tag)
    elif args.action == "run":
        run_container(args.tag, args.port)
    elif args.action == "stop":
        stop_container()
    elif args.action == "remove":
        remove_container()
    elif args.action == "compose":
        if not check_docker_compose_installed():
            print("Docker Compose is required but not installed")
            sys.exit(1)
        run_with_compose(args.profile)
    elif args.action == "stop-compose":
        stop_compose()
    elif args.action == "logs":
        show_logs(follow=args.follow)
    elif args.action == "status":
        show_status()
    elif args.action == "cleanup":
        clean_up()

if __name__ == "__main__":
    main() 