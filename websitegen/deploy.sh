#!/bin/bash

# Academic Website Build & Deploy Script

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_SCRIPT="build_site.py"
OUTPUT_DIR="dist"
TARGET_DIR="../"  # Directory to copy the built site (one level up by default)
GIT_BRANCH="main" # Default branch to push to

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo -e "${YELLOW}Usage: $0 [options]${NC}"
    echo "Options:"
    echo "  -n, --no-copy      Build without copying to target directory"
    echo "  -c, --commit       Automatically commit changes with timestamp"
    echo "  -p, --push         Push to remote repository after commit"
    echo "  -m <message>, --message=<message>  Custom commit message"
    echo "  -b <branch>, --branch=<branch>     Specify git branch (default: main)"
    echo "  -h, --help         Show this help message"
    exit 1
}

# Parse command line options
NO_COPY=false
AUTO_COMMIT=false
AUTO_PUSH=false
COMMIT_MESSAGE=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -n|--no-copy) NO_COPY=true ;;
        -c|--commit) AUTO_COMMIT=true ;;
        -p|--push) AUTO_PUSH=true ;;
        -m|--message) COMMIT_MESSAGE="$2"; shift ;;
        -b|--branch) GIT_BRANCH="$2"; shift ;;
        -h|--help) usage ;;
        *) echo -e "${RED}Unknown parameter: $1${NC}"; usage ;;
    esac
    shift
done

# Build the site
build_site() {
    echo -e "${GREEN}Building site...${NC}"
    cd "$PROJECT_DIR" || exit 1
    python3 "$BUILD_SCRIPT"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Build failed!${NC}"
        exit 1
    fi
}

# Copy the output
copy_output() {
    if [ "$NO_COPY" = false ]; then
        echo -e "${GREEN}Copying output to target directory...${NC}"
        rsync -av --delete "$PROJECT_DIR/$OUTPUT_DIR/" "$TARGET_DIR"
    else
        echo -e "${YELLOW}Skipping copy to target directory${NC}"
    fi
}

# Git operations
git_operations() {
    if [ "$AUTO_COMMIT" = true ]; then
        cd "$PROJECT_DIR" || exit 1
        
        # Generate commit message if not provided
        if [ -z "$COMMIT_MESSAGE" ]; then
            TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
            COMMIT_MESSAGE="Site update: $TIMESTAMP"
        fi
        
        echo -e "${GREEN}Committing changes...${NC}"
        git add .
        git commit -m "$COMMIT_MESSAGE"
        
        if [ "$AUTO_PUSH" = true ]; then
            echo -e "${GREEN}Pushing to ${GIT_BRANCH}...${NC}"
            git push origin "$GIT_BRANCH"
        fi
    fi
}

# Main execution
main() {
    build_site
    copy_output
    git_operations
    echo -e "${GREEN}Deployment complete!${NC}"
}

main
