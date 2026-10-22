#!/usr/bin/env bash
# ==============================================================================
# Oracle Cloud Always-Free Deployment Script for PARIVESH 2.0 KYA Backend
# Region: India (Mumbai / Hyderabad)
# ==============================================================================
set -e

echo "=== 1. Updating System Packages ==="
sudo apt-get update -y
sudo apt-get install -y git curl iptables iptables-persistent ca-certificates

echo "=== 2. Installing Docker & Docker Compose ==="
if ! command -v docker &> /dev/null; then
    sudo apt-get install -y docker.io docker-compose-v2
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$USER" || true
fi

echo "=== 3. Opening Oracle VM Firewall Ports (80 & 8000) ==="
# Oracle Ubuntu images have restrictive default iptables rules
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT 2>/dev/null || true
sudo netfilter-persistent save 2>/dev/null || true

echo "=== 4. Launching Backend Container ==="
sudo docker compose up -d --build

echo ""
echo "=========================================================================="
echo "SUCCESS! PARIVESH 2.0 Backend is now running on Oracle Cloud India!"
echo "Check health: curl http://localhost/api/v1/health"
echo "Public endpoint: http://<YOUR_ORACLE_PUBLIC_IP>/api/v1/health"
echo "=========================================================================="
