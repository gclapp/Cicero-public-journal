#!/bin/bash
# Install Go for ARM64 Linux

echo "Downloading Go 1.21.0 for ARM64..."
wget -q --show-progress https://go.dev/dl/go1.21.0.linux-arm64.tar.gz

echo "Removing any existing Go installation..."
sudo rm -rf /usr/local/go

echo "Extracting to /usr/local..."
sudo tar -C /usr/local -xzf go1.21.0.linux-arm64.tar.gz

echo "Cleaning up..."
rm go1.21.0.linux-arm64.tar.gz

echo "Adding Go to PATH..."
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc

# For current session
export PATH=$PATH:/usr/local/go/bin

echo "Verifying installation..."
/usr/local/go/bin/go version

echo "Done! Run 'source ~/.bashrc' or open a new terminal to use go."
