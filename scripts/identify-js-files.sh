#!/bin/bash

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN} JavaScript to TypeScript Migration File Finder ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""

# Check current directory
if [ ! -d "./frontend" ]; then
  echo -e "${RED}Error: Must be run from the root of the project.${NC}"
  echo "Current directory: $(pwd)"
  exit 1
fi

echo -e "${BLUE}Scanning for JavaScript files that need migration...${NC}"
echo ""

# Create output directory for reports
REPORT_DIR="./migration-reports"
mkdir -p $REPORT_DIR

# Get current date for report filename
CURRENT_DATE=$(date +"%Y%m%d")
REPORT_FILE="$REPORT_DIR/js-files-to-migrate-$CURRENT_DATE.md"

# Initialize report file
echo "# JavaScript Files To Migrate" > $REPORT_FILE
echo "" >> $REPORT_FILE
echo "Report generated on $(date)" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Check pages directory
echo -e "${YELLOW}Checking pages directory...${NC}"
echo "## Pages" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Find JavaScript pages and check if TypeScript version exists
find ./frontend/pages -name "*.js" | sort | while read jsfile; do
  filename=$(basename "$jsfile" .js)
  filepath=$(dirname "$jsfile")
  tsfile="./frontend/src/pages/${filename}.tsx"
  
  if [ -f "$tsfile" ]; then
    echo -e "- [${GREEN}✓${NC}] $jsfile (TypeScript version exists)"
    echo "- [x] \`${jsfile}\` - TypeScript version exists" >> $REPORT_FILE
  else
    echo -e "- [${RED}✗${NC}] $jsfile (No TypeScript version)"
    echo "- [ ] \`${jsfile}\` - No TypeScript version" >> $REPORT_FILE
  fi
done

echo "" >> $REPORT_FILE

# Check components directory
echo -e "\n${YELLOW}Checking components directory...${NC}"
echo "## Components" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Find JavaScript components and check if TypeScript version exists
find ./frontend/components -name "*.js" | sort | while read jsfile; do
  filename=$(basename "$jsfile" .js)
  filepath=$(dirname "$jsfile")
  
  # Extract relative path from components directory
  relpath=${filepath#"./frontend/components/"}
  if [ "$relpath" != "$filepath" ]; then
    # If in a subdirectory
    if [ "$relpath" != "" ]; then
      tsfile="./frontend/src/components/${relpath}/${filename}.tsx"
    else
      tsfile="./frontend/src/components/${filename}.tsx"
    fi
  else
    tsfile="./frontend/src/components/${filename}.tsx"
  fi
  
  if [ -f "$tsfile" ]; then
    echo -e "- [${GREEN}✓${NC}] $jsfile (TypeScript version exists)"
    echo "- [x] \`${jsfile}\` - TypeScript version exists" >> $REPORT_FILE
  else
    echo -e "- [${RED}✗${NC}] $jsfile (No TypeScript version)"
    echo "- [ ] \`${jsfile}\` - No TypeScript version" >> $REPORT_FILE
  fi
done

echo "" >> $REPORT_FILE

# Check utils directory
echo -e "\n${YELLOW}Checking utilities...${NC}"
echo "## Utilities" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Find JavaScript utilities and check if TypeScript version exists
find ./frontend/lib -name "*.js" | sort | while read jsfile; do
  filename=$(basename "$jsfile" .js)
  filepath=$(dirname "$jsfile")
  
  # Extract relative path from lib directory
  relpath=${filepath#"./frontend/lib/"}
  if [ "$relpath" != "$filepath" ]; then
    # If in a subdirectory
    if [ "$relpath" != "" ]; then
      tsfile="./frontend/src/utils/${relpath}/${filename}.ts"
    else
      tsfile="./frontend/src/utils/${filename}.ts"
    fi
  else
    tsfile="./frontend/src/utils/${filename}.ts"
  fi
  
  if [ -f "$tsfile" ]; then
    echo -e "- [${GREEN}✓${NC}] $jsfile (TypeScript version exists)"
    echo "- [x] \`${jsfile}\` - TypeScript version exists" >> $REPORT_FILE
  else
    echo -e "- [${RED}✗${NC}] $jsfile (No TypeScript version)"
    echo "- [ ] \`${jsfile}\` - No TypeScript version" >> $REPORT_FILE
  fi
done

# Calculate statistics
TOTAL_JS_FILES=$(find ./frontend/pages ./frontend/components ./frontend/lib -name "*.js" | wc -l)
MIGRATED_JS_FILES=$(grep -c "\[x\]" $REPORT_FILE)
PENDING_JS_FILES=$((TOTAL_JS_FILES - MIGRATED_JS_FILES))
PERCENT_DONE=$((MIGRATED_JS_FILES * 100 / TOTAL_JS_FILES))

echo -e "\n${BLUE}Migration Statistics:${NC}"
echo -e "- Total JavaScript files: ${TOTAL_JS_FILES}"
echo -e "- Files with TypeScript versions: ${GREEN}${MIGRATED_JS_FILES}${NC}"
echo -e "- Files pending migration: ${RED}${PENDING_JS_FILES}${NC}"
echo -e "- Migration progress: ${GREEN}${PERCENT_DONE}%${NC}"

echo -e "\n## Migration Statistics" >> $REPORT_FILE
echo -e "- **Total JavaScript files:** ${TOTAL_JS_FILES}" >> $REPORT_FILE
echo -e "- **Files with TypeScript versions:** ${MIGRATED_JS_FILES}" >> $REPORT_FILE
echo -e "- **Files pending migration:** ${PENDING_JS_FILES}" >> $REPORT_FILE
echo -e "- **Migration progress:** ${PERCENT_DONE}%" >> $REPORT_FILE

echo -e "\n${GREEN}Report saved to: ${REPORT_FILE}${NC}"
echo -e "${GREEN}==================================================${NC}" 