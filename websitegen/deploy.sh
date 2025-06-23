#!/bin/bash

# Academic Website Build & Deploy Script

# Function to display usage information
usage() {
    echo "Usage: $0 [-b <build_script>] [-d <destination>] [-g] [-h]"
    echo "  -b <build_script> : Specify the build script to run (default: build_site.py)"
    echo "  -d <destination>  : Specify the destination directory to copy the build output"
    echo "  -g                : Perform git add, commit, and push operations"
    echo "  -h                : Display this help message"
    exit 1
}

# Default values
BUILD_SCRIPT="build_site.py"
DESTINATION=""
GIT_OPERATION=false

# Parse command-line arguments
while getopts ":b:d:gh" opt; do
    case ${opt} in
        b )
            BUILD_SCRIPT=$OPTARG
            ;;
        d )
            DESTINATION=$OPTARG
            ;;
        g )
            GIT_OPERATION=true
            ;;
        h )
            usage
            ;;
        \? )
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
        : )
            echo "Option -$OPTARG requires an argument." >&2
            usage
            ;;
    esac
done
shift $((OPTIND -1))

# Run the build script
echo "Running build script: $BUILD_SCRIPT"
python3 $BUILD_SCRIPT

if [ $? -ne 0 ]; then
    echo "Build failed. Exiting."
    exit 1
fi

# Copy the build output if a destination is specified
if [ -n "$DESTINATION" ]; then
    echo "Copying build output to: $DESTINATION"
    cp -r dist/* "$DESTINATION/"
    if [ $? -ne 0 ]; then
        echo "Copy failed. Exiting."
        exit 1
    fi
fi

# Perform Git operations if requested
if $GIT_OPERATION; then
    echo "Performing git operations..."
    git add .
    if [ $? -ne 0 ]; then
        echo "Git add failed. Exiting."
        exit 1
    fi

    read -p "Enter commit message: " COMMIT_MSG
    git commit -m "$COMMIT_MSG"
    if [ $? -ne 0 ]; then
        echo "Git commit failed. Exiting."
        exit 1
    fi

    git push
    if [ $? -ne 0 ]; then
        echo "Git push failed. Exiting."
        exit 1
    fi
fi

echo "Script completed successfully."
