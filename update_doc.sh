#!/bin/bash

# Script Description: Replace content surrounded by specific comments in all md files with corresponding file content
# Universal format: <!-- filename --> content <!-- /filename -->
# The script will automatically detect all comment tags in this format and replace them with the corresponding file content

# ===============================
# File Sync Configuration Area - Add files to sync here
# ===============================
# Format: filename:code_type (separated by colon)
# If code_type is not specified, the script will automatically infer it based on file extension

# Files to sync (format: "filename:code_type")
FILES_TO_SYNC=(
    "docker-compose-example.yml:yaml"
    ".env.example:env"
    # Add more files, uncomment and modify the following examples:
    # "package.json:json"
    # "requirements.txt:text"
    # "Dockerfile:dockerfile"
    # "nginx.conf:nginx"
    # "config.yaml:yaml"
    # "startup.sh:bash"
)

# ===============================
# Script Function Area
# ===============================

# Get filename from config entry
get_filename() {
    echo "$1" | cut -d: -f1
}

# Get code type from config entry
get_configured_code_type() {
    local entry="$1"
    if [[ "$entry" == *":"* ]]; then
        echo "$entry" | cut -d: -f2
    else
        echo ""
    fi
}

# Infer code type based on file extension
get_code_type() {
    local filename="$1"
    local extension="${filename##*.}"
    
    case "$extension" in
        yml|yaml) echo "yaml" ;;
        json) echo "json" ;;
        js|mjs) echo "javascript" ;;
        ts) echo "typescript" ;;
        py) echo "python" ;;
        sh|bash) echo "bash" ;;
        css) echo "css" ;;
        html|htm) echo "html" ;;
        xml) echo "xml" ;;
        sql) echo "sql" ;;
        md) echo "markdown" ;;
        txt|log|conf|config) echo "text" ;;
        env|example) echo "env" ;;
        dockerfile) echo "dockerfile" ;;
        nginx) echo "nginx" ;;
        *) echo "text" ;;
    esac
}

# Function to check if file exists
check_file_exists() {
    local file_path="$1"
    if [ ! -f "$file_path" ]; then
        echo "Warning: $file_path does not exist, skipping"
        return 1
    fi
    return 0
}

# Function to process file replacement
process_file() {
    local md_file="$1"
    local source_file="$2"
    local start_tag="$3"
    local end_tag="$4"
    local code_type="$5"
    
    echo "Processing file: $md_file (replacing with $source_file content)"
    
    # Temporary file
    temp_file=$(mktemp)
    
    # Use awk to replace content
    awk -v source_file="$source_file" -v start_tag="$start_tag" -v end_tag="$end_tag" -v code_type="$code_type" '
    BEGIN { 
        in_block = 0
        # Read source file content
        while ((getline line < source_file) > 0) {
            source_content = source_content line "\n"
        }
        close(source_file)
    }
    $0 ~ start_tag {
        print $0
        print "```" code_type
        printf "%s", source_content
        print "```"
        in_block = 1
        next
    }
    $0 ~ end_tag {
        in_block = 0
        print $0
        next
    }
    !in_block {
        print $0
    }
    ' "$md_file" > "$temp_file"
    
    # Replace original file
    mv "$temp_file" "$md_file"
    echo "Updated: $md_file"
}

# ===============================
# Main Program
# ===============================

echo "Starting document update process..."
echo ""

# Display configured file list
echo "Configured file list:"
for entry in "${FILES_TO_SYNC[@]}"; do
    filename=$(get_filename "$entry")
    code_type=$(get_configured_code_type "$entry")
    if [ -f "$filename" ]; then
        echo "  ✓ $filename ($code_type)"
    else
        echo "  ✗ $filename ($code_type) - file not found"
    fi
done

echo ""
echo "Starting file replacement process..."

# Process each md file (exclude .venv, .git, node_modules directories)
find . -name "*.md" -type f \
    -not -path "./.venv/*" \
    -not -path "./.git/*" \
    -not -path "./node_modules/*" \
    -not -path "./*/.venv/*" \
    -not -path "./*/.git/*" \
    -not -path "./*/node_modules/*" \
    | while read -r md_file; do
    echo "Checking file: $md_file"
    
    file_updated=false
    
    # Check configured file list
    for entry in "${FILES_TO_SYNC[@]}"; do
        source_file=$(get_filename "$entry")
        
        # Check if start and end tags exist
        if grep -q "<!-- $source_file -->" "$md_file" && grep -q "<!-- /$source_file -->" "$md_file"; then
            # Check if source file exists
            if check_file_exists "$source_file"; then
                # Get code type (prioritize configured type, otherwise auto-infer)
                code_type=$(get_configured_code_type "$entry")
                if [ -z "$code_type" ]; then
                    code_type=$(get_code_type "$source_file")
                fi
                
                # Process file
                process_file "$md_file" "$source_file" "<!-- $source_file -->" "<!-- /$source_file -->" "$code_type"
                file_updated=true
            fi
        fi
    done
    
    if [ "$file_updated" = false ]; then
        echo "Skipping file: $md_file (no configured file reference tags found)"
    fi
done

echo ""
echo "Script execution completed!"
echo ""
echo "Usage Instructions:"
echo "1. Add files to sync in the FILES_TO_SYNC array at the top of the script"
echo "2. Use format in markdown files: <!-- filename --> ... <!-- /filename -->"
echo "3. Run the script to automatically sync content"
echo ""
echo "Supported code types:"
echo "  yaml, json, javascript, typescript, python, bash, css, html, xml, sql, markdown, env, dockerfile, nginx, text"
echo ""
echo "Ignored directories:"
echo "  .venv, .git, node_modules (and their subdirectories)"
