# DynamoDB Local Viewer Script
# Lists all tables and their details from DynamoDB Local running on localhost:8000

param(
    [string]$Endpoint = "http://localhost:8000",
    [switch]$Detailed,
    [string]$TableName = $null
)

# Set AWS CLI to use local DynamoDB
$env:AWS_ACCESS_KEY_ID = "dummy"
$env:AWS_SECRET_ACCESS_KEY = "dummy"
$env:AWS_DEFAULT_REGION = "us-west-2"

Write-Host "DynamoDB Local Viewer" -ForegroundColor Green
Write-Host "Endpoint: $Endpoint" -ForegroundColor Yellow
Write-Host "=" * 50

try {
    # Test connection to DynamoDB Local
    aws dynamodb list-tables --endpoint-url $Endpoint --output json 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Cannot connect to DynamoDB Local at $Endpoint" -ForegroundColor Red
        Write-Host "Make sure DynamoDB Local is running with:" -ForegroundColor Yellow
        Write-Host "  java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb" -ForegroundColor Cyan
        exit 1
    }

    # Get list of tables
    $tablesJson = aws dynamodb list-tables --endpoint-url $Endpoint --output json
    $tables = ($tablesJson | ConvertFrom-Json).TableNames

    if ($tables.Count -eq 0) {
        Write-Host "No tables found in DynamoDB Local" -ForegroundColor Yellow
        exit 0
    }

    Write-Host "Found $($tables.Count) table(s):" -ForegroundColor Green
    Write-Host ""

    # If specific table requested
    if ($TableName) {
        if ($TableName -notin $tables) {
            Write-Host "Table '$TableName' not found" -ForegroundColor Red
            Write-Host "Available tables: $($tables -join ', ')" -ForegroundColor Yellow
            exit 1
        }
        $tables = @($TableName)
    }

    foreach ($table in $tables) {
        Write-Host "Table: $table" -ForegroundColor Cyan
        Write-Host "-" * 40

        # Get table description
        $describeJson = aws dynamodb describe-table --table-name $table --endpoint-url $Endpoint --output json
        $tableInfo = ($describeJson | ConvertFrom-Json).Table

        # Basic table info
        Write-Host "  Status: $($tableInfo.TableStatus)" -ForegroundColor $(if($tableInfo.TableStatus -eq "ACTIVE") {"Green"} else {"Yellow"})
        Write-Host "  Item Count: $($tableInfo.ItemCount)"
        Write-Host "  Size (bytes): $($tableInfo.TableSizeBytes)"
        Write-Host "  Created: $($tableInfo.CreationDateTime)"

        # Key schema
        Write-Host "  Key Schema:" -ForegroundColor Yellow
        foreach ($key in $tableInfo.KeySchema) {
            $attrType = ($tableInfo.AttributeDefinitions | Where-Object {$_.AttributeName -eq $key.AttributeName}).AttributeType
            Write-Host "    $($key.AttributeName) ($attrType) - $($key.KeyType)" -ForegroundColor White
        }

        # Global Secondary Indexes
        if ($tableInfo.GlobalSecondaryIndexes) {
            Write-Host "  Global Secondary Indexes:" -ForegroundColor Yellow
            foreach ($gsi in $tableInfo.GlobalSecondaryIndexes) {
                Write-Host "    $($gsi.IndexName) - Status: $($gsi.IndexStatus)" -ForegroundColor White
            }
        }

        # Show sample items if detailed flag is set
        if ($Detailed) {
            Write-Host "  Sample Items (first 5):" -ForegroundColor Yellow
            try {
                $scanJson = aws dynamodb scan --table-name $table --limit 5 --endpoint-url $Endpoint --output json 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $items = ($scanJson | ConvertFrom-Json).Items
                    if ($items.Count -gt 0) {
                        foreach ($item in $items) {
                            $simplifiedItem = @{}
                            foreach ($attr in $item.PSObject.Properties) {
                                $value = $attr.Value
                                if ($value.S) { $simplifiedItem[$attr.Name] = $value.S }
                                elseif ($value.N) { $simplifiedItem[$attr.Name] = [int]$value.N }
                                elseif ($value.B) { $simplifiedItem[$attr.Name] = "[Binary]" }
                                elseif ($value.SS) { $simplifiedItem[$attr.Name] = $value.SS }
                                elseif ($value.NS) { $simplifiedItem[$attr.Name] = $value.NS }
                                elseif ($value.M) { $simplifiedItem[$attr.Name] = "[Map]" }
                                elseif ($value.L) { $simplifiedItem[$attr.Name] = "[List]" }
                                else { $simplifiedItem[$attr.Name] = $value }
                            }
                            Write-Host "    $(($simplifiedItem | ConvertTo-Json -Compress))" -ForegroundColor Gray
                        }
                    } else {
                        Write-Host "    (No items found)" -ForegroundColor Gray
                    }
                } else {
                    Write-Host "    (Error scanning table)" -ForegroundColor Red
                }
            } catch {
                Write-Host "    (Error retrieving items: $($_.Exception.Message))" -ForegroundColor Red
            }
        }

        Write-Host ""
    }

    # Summary
    Write-Host "Summary:" -ForegroundColor Green
    Write-Host "  Total Tables: $($tables.Count)"
    
    if ($Detailed) {
        Write-Host ""
        Write-Host "Tips:" -ForegroundColor Yellow
        Write-Host "  - Use -TableName <name> to view specific table"
        Write-Host "  - Use AWS CLI for more operations:"
        Write-Host "    aws dynamodb scan --table-name <table> --endpoint-url $Endpoint"
        Write-Host "    aws dynamodb put-item --table-name <table> --item '{...}' --endpoint-url $Endpoint"
    } else {
        Write-Host "  Use -Detailed flag to see sample items"
    }

} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
