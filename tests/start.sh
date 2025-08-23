#!/bin/bash
# filepath: /Users/jbarwick/Development/simple-cloud-kit/sck-core-db/tests/start.sh
# DynamoDB Local Startup Script
# Manages Docker Compose services for Simple Cloud Kit Database Testing

# Default values
ACTION="start"
DETACHED=true
WITH_ADMIN=false
WITH_TOOLS=false
FOLLOW=false
SERVICE=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    echo -e "${1}${2}${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        start|stop|restart|status|logs|clean|admin|tools)
            ACTION="$1"
            shift
            ;;
        --detached)
            DETACHED=true
            shift
            ;;
        --no-detached)
            DETACHED=false
            shift
            ;;
        --with-admin)
            WITH_ADMIN=true
            shift
            ;;
        --with-tools)
            WITH_TOOLS=true
            shift
            ;;
        --follow)
            FOLLOW=true
            shift
            ;;
        --service)
            SERVICE="$2"
            shift 2
            ;;
        -h|--help)
            ACTION="help"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            ACTION="help"
            shift
            ;;
    esac
done

# Set location to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_color $GREEN "Simple Cloud Kit - DynamoDB Local Manager"
echo "=================================================="

# Check if Docker is running
test_docker_running() {
    if ! docker version >/dev/null 2>&1; then
        print_color $RED "ERROR: Docker is not running or not installed"
        print_color $YELLOW "Please start Docker Desktop and try again"
        return 1
    fi
    return 0
}

# Check if Docker Compose is available
test_docker_compose() {
    if docker-compose version >/dev/null 2>&1; then
        return 0
    elif docker compose version >/dev/null 2>&1; then
        return 0
    else
        print_color $RED "ERROR: Docker Compose is not available"
        return 1
    fi
}

# Get the appropriate Docker Compose command
get_docker_compose_cmd() {
    if docker-compose version >/dev/null 2>&1; then
        echo "docker-compose"
    else
        echo "docker compose"
    fi
}

# Create data directory if it doesn't exist
initialize_data_directory() {
    local data_dir="$SCRIPT_DIR/dynamodb-data"
    if [[ ! -d "$data_dir" ]]; then
        print_color $YELLOW "Creating data directory: $data_dir"
        mkdir -p "$data_dir"
    fi
}

# Test URL health
test_url_health() {
    local url="$1"
    local name="$2"
    
    if curl -s --max-time 5 "$url" >/dev/null 2>&1; then
        print_color $GREEN "✓ $name: Healthy"
    else
        print_color $RED "✗ $name: Unhealthy"
    fi
}

# Show usage
show_usage() {
    print_color $YELLOW "Usage: ./start.sh [action] [options]"
    echo
    print_color $CYAN "Actions:"
    print_color $WHITE "  start     Start DynamoDB Local (default)"
    print_color $WHITE "  stop      Stop all services"
    print_color $WHITE "  restart   Restart services"
    print_color $WHITE "  status    Show service status and health"
    print_color $WHITE "  logs      Show service logs"
    print_color $WHITE "  clean     Stop services and remove all data"
    print_color $WHITE "  admin     Start with Admin UI"
    print_color $WHITE "  tools     Start with all tools"
    echo
    print_color $CYAN "Options:"
    print_color $WHITE "  --with-admin      Include DynamoDB Admin UI"
    print_color $WHITE "  --with-tools      Include AWS CLI tools"
    print_color $WHITE "  --follow          Follow logs (for logs action)"
    print_color $WHITE "  --service SERVICE Target specific service"
    print_color $WHITE "  --no-detached     Run in foreground"
    echo
    print_color $CYAN "Examples:"
    print_color $WHITE "  ./start.sh                      # Start DynamoDB Local only"
    print_color $WHITE "  ./start.sh admin                # Start with Admin UI"
    print_color $WHITE "  ./start.sh start --with-admin   # Start with Admin UI"
    print_color $WHITE "  ./start.sh logs --follow        # Follow logs"
    print_color $WHITE "  ./start.sh status               # Check health"
    print_color $WHITE "  ./start.sh clean                # Clean everything"
}

# Main script logic
if ! test_docker_running; then
    exit 1
fi

if ! test_docker_compose; then
    exit 1
fi

DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
print_color $CYAN "Using: $DOCKER_COMPOSE_CMD"

# Build compose arguments
COMPOSE_ARGS=()
if [[ "$WITH_TOOLS" == "true" ]]; then
    COMPOSE_ARGS+=(--profile tools)
fi

case "$(echo "$ACTION" | tr '[:upper:]' '[:lower:]')" in
    "start")
        print_color $YELLOW "Starting DynamoDB Local services..."
        
        initialize_data_directory
        
        SERVICES=("dynamodb-local")
        if [[ "$WITH_ADMIN" == "true" ]]; then
            SERVICES+=("dynamodb-admin")
        fi
        
        START_ARGS=("${COMPOSE_ARGS[@]}" "up")
        if [[ "$DETACHED" == "true" ]]; then
            START_ARGS+=("-d")
        fi
        START_ARGS+=("${SERVICES[@]}")
        
        if $DOCKER_COMPOSE_CMD "${START_ARGS[@]}"; then
            echo
            print_color $GREEN "Services started successfully!"
            print_color $CYAN "DynamoDB Local: http://localhost:8000"
            if [[ "$WITH_ADMIN" == "true" ]]; then
                print_color $CYAN "DynamoDB Admin: http://localhost:8001"
            fi
            echo
            print_color $YELLOW "Test connection with:"
            print_color $WHITE "  ./view.sh"
            echo
            print_color $YELLOW "Useful commands:"
            print_color $WHITE "  ./start.sh status    - Check service status"
            print_color $WHITE "  ./start.sh logs      - View logs"
            print_color $WHITE "  ./start.sh stop      - Stop services"
        fi
        ;;
        
    "stop")
        print_color $YELLOW "Stopping DynamoDB Local services..."
        if $DOCKER_COMPOSE_CMD "${COMPOSE_ARGS[@]}" down; then
            print_color $GREEN "Services stopped successfully!"
        fi
        ;;
        
    "restart")
        print_color $YELLOW "Restarting DynamoDB Local services..."
        RESTART_ARGS=("${COMPOSE_ARGS[@]}" "restart")
        if [[ -n "$SERVICE" ]]; then
            RESTART_ARGS+=("$SERVICE")
        fi
        
        if $DOCKER_COMPOSE_CMD "${RESTART_ARGS[@]}"; then
            print_color $GREEN "Services restarted successfully!"
        fi
        ;;
        
    "status")
        print_color $YELLOW "Service Status:"
        $DOCKER_COMPOSE_CMD "${COMPOSE_ARGS[@]}" ps
        
        echo
        print_color $YELLOW "Container Health:"
        test_url_health "http://localhost:8000/" "DynamoDB Local"
        
        if [[ "$WITH_ADMIN" == "true" ]]; then
            test_url_health "http://localhost:8001/" "DynamoDB Admin"
        fi
        ;;
        
    "logs")
        print_color $YELLOW "Viewing logs..."
        LOG_ARGS=("${COMPOSE_ARGS[@]}" "logs")
        if [[ "$FOLLOW" == "true" ]]; then
            LOG_ARGS+=("-f")
        fi
        if [[ -n "$SERVICE" ]]; then
            LOG_ARGS+=("$SERVICE")
        fi
        
        $DOCKER_COMPOSE_CMD "${LOG_ARGS[@]}"
        ;;
        
    "clean")
        print_color $YELLOW "Cleaning up DynamoDB Local data and containers..."
        print_color $RED "WARNING: This will delete all data!"
        
        read -p "Are you sure? (y/N): " -n 1 -r CONFIRM
        echo
        if [[ $CONFIRM =~ ^[Yy]$ ]]; then
            $DOCKER_COMPOSE_CMD "${COMPOSE_ARGS[@]}" down -v --remove-orphans
            
            DATA_DIR="$SCRIPT_DIR/dynamodb-data"
            if [[ -d "$DATA_DIR" ]]; then
                print_color $YELLOW "Removing data directory..."
                rm -rf "$DATA_DIR"
            fi
            
            print_color $GREEN "Cleanup completed!"
        else
            print_color $YELLOW "Cleanup cancelled"
        fi
        ;;
        
    "admin")
        print_color $YELLOW "Starting with DynamoDB Admin UI..."
        WITH_ADMIN=true
        ACTION="start"
        # Re-run with start action
        exec "$0" start --with-admin "${@:2}"
        ;;
        
    "tools")
        print_color $YELLOW "Starting with all tools..."
        WITH_ADMIN=true
        WITH_TOOLS=true
        ACTION="start"
        # Re-run with start action
        exec "$0" start --with-admin --with-tools "${@:2}"
        ;;
        
    "help"|*)
        show_usage
        ;;
esac