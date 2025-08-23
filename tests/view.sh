#!/bin/bash
# filepath: /Users/jbarwick/Development/simple-cloud-kit/sck-core-db/tests/view.sh
# DynamoDB Local Viewer Script
# Lists all tables and their details from DynamoDB Local running on localhost:8000

# Default values
ENDPOINT="http://localhost:8000"
DETAILED=false
TABLE_NAME=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    echo -e "${1}${2}${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --endpoint)
            ENDPOINT="$2"
            shift 2
            ;;
        --detailed)
            DETAILED=true
            shift
            ;;
        --table-name)
            TABLE_NAME="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --endpoint URL      DynamoDB endpoint (default: http://localhost:8000)"
            echo "  --detailed          Show detailed information including sample items"
            echo "  --table-name NAME   View specific table only"
            echo "  -h, --help          Show this help message"
            echo
            echo "Examples:"
            echo "  $0                                    # List all tables"
            echo "  $0 --detailed                        # List all tables with sample data"
            echo "  $0 --table-name MyTable              # View specific table"
            echo "  $0 --endpoint http://localhost:8001  # Use different endpoint"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set AWS CLI to use local DynamoDB
export AWS_ACCESS_KEY_ID="dummy"
export AWS_SECRET_ACCESS_KEY="dummy"
export AWS_DEFAULT_REGION="us-west-2"

print_color $GREEN "DynamoDB Local Viewer"
print_color $YELLOW "Endpoint: $ENDPOINT"
echo "=================================================="

# Function to check if jq is available
check_jq() {
    if ! command -v jq &> /dev/null; then
        print_color $RED "ERROR: jq is required but not installed"
        print_color $YELLOW "Install with: brew install jq (macOS) or apt-get install jq (Ubuntu)"
        exit 1
    fi
}

# Function to test connection to DynamoDB Local
test_connection() {
    if ! aws dynamodb list-tables --endpoint-url "$ENDPOINT" --output json >/dev/null 2>&1; then
        print_color $RED "ERROR: Cannot connect to DynamoDB Local at $ENDPOINT"
        print_color $YELLOW "Make sure DynamoDB Local is running with:"
        print_color $CYAN "  java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb"
        print_color $YELLOW "Or use Docker:"
        print_color $CYAN "  ./start.sh"
        exit 1
    fi
}

# Function to get table count from JSON
get_table_count() {
    local json="$1"
    echo "$json" | jq -r '.TableNames | length'
}

# Function to get table names from JSON
get_table_names() {
    local json="$1"
    echo "$json" | jq -r '.TableNames[]'
}

# Function to simplify DynamoDB item for display
simplify_item() {
    local item="$1"
    echo "$item" | jq -r 'to_entries | map(
        if .value.S then {key: .key, value: .value.S}
        elif .value.N then {key: .key, value: (.value.N | tonumber)}
        elif .value.B then {key: .key, value: "[Binary]"}
        elif .value.SS then {key: .key, value: .value.SS}
        elif .value.NS then {key: .key, value: .value.NS}
        elif .value.M then {key: .key, value: "[Map]"}
        elif .value.L then {key: .key, value: "[List]"}
        else {key: .key, value: .value}
        end
    ) | from_entries'
}

# Function to get status color
get_status_color() {
    local status="$1"
    if [[ "$status" == "ACTIVE" ]]; then
        echo "$GREEN"
    else
        echo "$YELLOW"
    fi
}

# Check dependencies
check_jq

# Test connection
test_connection

# Get list of tables
tables_json=$(aws dynamodb list-tables --endpoint-url "$ENDPOINT" --output json)
table_count=$(get_table_count "$tables_json")

if [[ "$table_count" -eq 0 ]]; then
    print_color $YELLOW "No tables found in DynamoDB Local"
    exit 0
fi

print_color $GREEN "Found $table_count table(s):"
echo

# Get table names into array (most compatible)
tables=()
table_names=$(get_table_names "$tables_json")
while IFS= read -r table; do
    [[ -n "$table" ]] && tables+=("$table")
done <<< "$table_names"

# Debug: Print what we got
if [[ ${#tables[@]} -eq 0 ]]; then
    print_color $RED "DEBUG: No tables were loaded into array"
    print_color $YELLOW "Raw table names output:"
    echo "$table_names"
    exit 1
fi

# Output the list of found tables
for table in "${tables[@]}"; do
    print_color $WHITE "  • $table"
done
echo

# If specific table requested
if [[ -n "$TABLE_NAME" ]]; then
    table_found=false
    for table in "${tables[@]}"; do
        if [[ "$table" == "$TABLE_NAME" ]]; then
            table_found=true
            break
        fi
    done
    
    if [[ "$table_found" == false ]]; then
        print_color $RED "Table '$TABLE_NAME' not found"
        print_color $YELLOW "Available tables: $(IFS=', '; echo "${tables[*]}")"
        exit 1
    fi
    tables=("$TABLE_NAME")
fi

# Process each table
for table in "${tables[@]}"; do
    print_color $CYAN "Table: $table"
    echo "----------------------------------------"
    
    # Get table description
    describe_json=$(aws dynamodb describe-table --table-name "$table" --endpoint-url "$ENDPOINT" --output json)
    
    # Extract basic info using jq
    status=$(echo "$describe_json" | jq -r '.Table.TableStatus')
    item_count=$(echo "$describe_json" | jq -r '.Table.ItemCount')
    table_size=$(echo "$describe_json" | jq -r '.Table.TableSizeBytes')
    creation_date=$(echo "$describe_json" | jq -r '.Table.CreationDateTime')
    
    # Display basic table info
    status_color=$(get_status_color "$status")
    print_color "${status_color}" "  Status: $status"
    echo "  Item Count: $item_count"
    echo "  Size (bytes): $table_size"
    echo "  Created: $creation_date"
    
    # Key schema
    print_color $YELLOW "  Key Schema:"
    echo "$describe_json" | jq -r '.Table.KeySchema[] as $key | 
        .Table.AttributeDefinitions[] as $attr | 
        select($attr.AttributeName == $key.AttributeName) | 
        "    \($key.AttributeName) (\($attr.AttributeType)) - \($key.KeyType)"' | \
    while IFS= read -r line; do
        print_color $WHITE "$line"
    done
    
    # Global Secondary Indexes
    gsi_count=$(echo "$describe_json" | jq -r '.Table.GlobalSecondaryIndexes | length // 0')
    if [[ "$gsi_count" -gt 0 ]]; then
        print_color $YELLOW "  Global Secondary Indexes:"
        echo "$describe_json" | jq -r '.Table.GlobalSecondaryIndexes[]? | 
            "    \(.IndexName) - Status: \(.IndexStatus)"' | \
        while IFS= read -r line; do
            print_color $WHITE "$line"
        done
    fi
    
    # Show sample items if detailed flag is set
    if [[ "$DETAILED" == true ]]; then
        print_color $YELLOW "  Sample Items (first 5):"
        
        if scan_json=$(aws dynamodb scan --table-name "$table" --limit 5 --endpoint-url "$ENDPOINT" --output json 2>/dev/null); then
            item_count=$(echo "$scan_json" | jq -r '.Items | length')
            
            if [[ "$item_count" -gt 0 ]]; then
                echo "$scan_json" | jq -c '.Items[]' | while IFS= read -r item; do
                    simplified=$(simplify_item "$item")
                    print_color $GRAY "    $simplified"
                done
            else
                print_color $GRAY "    (No items found)"
            fi
        else
            print_color $RED "    (Error scanning table)"
        fi
    fi
    
    echo
done

# Summary
print_color $GREEN "Summary:"
echo "  Total Tables: ${#tables[@]}"

if [[ "$DETAILED" == true ]]; then
    echo
    print_color $YELLOW "Tips:"
    echo "  - Use --table-name <name> to view specific table"
    echo "  - Use AWS CLI for more operations:"
    echo "    aws dynamodb scan --table-name <table> --endpoint-url $ENDPOINT"
    echo "    aws dynamodb put-item --table-name <table> --item '{...}' --endpoint-url $ENDPOINT"
else
    echo "  Use --detailed flag to see sample items"
fi