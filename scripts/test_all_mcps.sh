#!/bin/bash

# Test script for running scrapers with different MCP implementations
echo "Testing scrapers with different MCP implementations"
echo "=================================================="
echo ""

# Create a results directory
mkdir -p scraper_test_results

# Function to run a scraper with a specific MCP type
run_scraper_test() {
    scraper_name=$1
    mcp_type=$2
    
    echo "Running $scraper_name with MCP type: $mcp_type"
    echo "------------------------------------------------"
    
    # Run the scraper with the specified MCP type and capture output
    output_file="scraper_test_results/${scraper_name}_${mcp_type}.log"
    
    MCP_SERVER_TYPE=$mcp_type python3 backend/run_${scraper_name}_scraper.py > $output_file 2>&1
    
    # Check for successful property extraction
    property_count=$(grep "Total properties extracted:" $output_file | awk '{print $NF}')
    
    # Check for errors or issues
    if grep -q "Error running" $output_file; then
        status="ERROR"
    elif grep -q "Access Denied" $output_file; then
        status="BLOCKED (Access Denied)"
    elif grep -q "Service unavailable" $output_file; then
        status="BLOCKED (Service Unavailable)"
    elif grep -q "Not Found" $output_file; then
        status="BLOCKED (404 Not Found)"
    elif grep -q "bot" $output_file; then
        status="BLOCKED (Bot Detection)"
    elif [ "$property_count" -gt "0" ]; then
        status="SUCCESS ($property_count properties)"
    else
        status="FAILED (0 properties)"
    fi
    
    echo "Status: $status"
    echo ""
    
    # Return the status for summary
    echo $status
}

# Scrapers and MCP types to test
scrapers=("walkerdunlop" "berkadia")
mcp_types=("firecrawl" "playwright" "puppeteer")

# Create results.txt file
echo "Summary of Results" > results.txt
echo "=================" >> results.txt
echo "" >> results.txt
echo "| Broker | Firecrawl | Playwright | Puppeteer |" >> results.txt
echo "|--------|-----------|------------|-----------|" >> results.txt

# Run tests for each scraper
for scraper in "${scrapers[@]}"; do
    # Format the scraper name for display
    if [ "$scraper" = "walkerdunlop" ]; then
        scraper_display_name="Walker & Dunlop"
    else
        scraper_display_name="Berkadia"
    fi
    
    # Start the line for this scraper
    echo -n "| $scraper_display_name | " >> results.txt
    
    # Run tests with each MCP type
    for mcp_type in "${mcp_types[@]}"; do
        # Run the test and get the status
        status=$(run_scraper_test $scraper $mcp_type)
        
        # Add the result to the line
        echo -n "$status | " >> results.txt
    done
    
    # End the line
    echo "" >> results.txt
done

# Display the results
cat results.txt

echo ""
echo "Test completed. Detailed logs are available in the scraper_test_results directory." 