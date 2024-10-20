#!/bin/bash

create_directory_structure() {
    local base_dir="$1"
    mkdir -p "$base_dir"/{original,processed/{guideline,api_specification}/{splitted_pdfs,analyzed_jsons,figures,tables}}
}

download_file() {
    local url="$1"
    local output="$2"
    curl -L -o "$output" "$url"
}

BASE_URL="https://www.mydatacenter.or.kr:3441/cmmn/fileBrDownload"
PARAMS=(
    "id=JHuKqjlWK0e%2FH9Yi7ed09GsZWL6TiRKp9yg4qGj%2FKFmV9RC6j8RJdh6I8JAqzoFv&type=2:guideline.pdf"
    "id=dKi%2B7cAM4PO8JA4z7jwm4AoM07vmQIbSKQ9EvM0DPRYokFCd%2BhLigsDUZ0hQopjD&type=2:api_specification.pdf"
)

main() {
    local resources_dir="resources"
    
    create_directory_structure "$resources_dir"
    
    cd "$resources_dir/original" || exit 1
    for param in "${PARAMS[@]}"; do
        IFS=':' read -r url_param filename <<< "$param"
        download_file "${BASE_URL}?${url_param}" "$filename"
    done
    
    if [ $? -eq 0 ]; then
        echo "Setup completed successfully!"
    else
        echo "Setup completed with some errors."
    fi
}

main