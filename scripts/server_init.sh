#!/bin/bash

set -e

echo "======================================="
echo " GlasHaus Secure Server Initialization "
echo "======================================="

# -----------------------------
# USER INPUT
# -----------------------------

read -p "Enter SSH Port (default 22): " SSH_PORT
SSH_PORT=${SSH_PORT:-22}

read -p "Enter new admin username: " ADMIN_USER

echo "Generate SSH-Key in your shell with: ssh-keygen -t ed25519 -C "glashaus-dev" -f ~/.ssh/glashaus_ed25519"
echo "safe it in your shell with: ~/.ssh/glashaus_ed25519"
echo "show your public key in your shell with: cat ~/.ssh/glashaus_ed25519.pub"

read -p "Paste your PUBLIC SSH key: " PUBLIC_KEY

read -p "WireGuard VPN subnet (default 10.0.0.0/24): " WG_SUBNET
WG_SUBNET=${WG_SUBNET:-10.0.0.0/24}

# -----------------------------
# SYSTEM UPDATE
# -----------------------------

sudo apt update && sudo apt upgrade -y

# -----------------------------
# INSTALL PACKAGES
# -----------------------------

sudo apt install -y \
    ufw \
    fail2ban \
    wireguard \
    curl \
    git \
    nginx

# -----------------------------
# CREATE ADMIN USER
# -----------------------------

sudo adduser --disabled-password --gecos "" $ADMIN_USER

sudo usermod -aG sudo $ADMIN_USER

# -----------------------------
# SSH SETUP
# -----------------------------

sudo mkdir -p /home/$ADMIN_USER/.ssh

echo "$PUBLIC_KEY" | sudo tee /home/$ADMIN_USER/.ssh/authorized_keys

sudo chmod 700 /home/$ADMIN_USER/.ssh
sudo chmod 600 /home/$ADMIN_USER/.ssh/authorized_keys

sudo chown -R $ADMIN_USER:$ADMIN_USER /home/$ADMIN_USER/.ssh

# -----------------------------
# SSH HARDENING
# -----------------------------

sudo sed -i "s/#Port 22/Port $SSH_PORT/" /etc/ssh/sshd_config

sudo sed -i "s/#PermitRootLogin prohibit-password/PermitRootLogin no/" /etc/ssh/sshd_config

sudo sed -i "s/#PasswordAuthentication yes/PasswordAuthentication no/" /etc/ssh/sshd_config

sudo systemctl restart ssh

# -----------------------------
# UFW FIREWALL
# -----------------------------

sudo ufw default deny incoming
sudo ufw default allow outgoing

sudo ufw allow $SSH_PORT/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 51820/udp

sudo ufw --force enable

# -----------------------------
# FAIL2BAN
# -----------------------------

cat <<EOF | sudo tee /etc/fail2ban/jail.local

[sshd]
enabled = true
port = $SSH_PORT
maxretry = 3
bantime = 1h

EOF

sudo systemctl restart fail2ban

# -----------------------------
# WIREGUARD SETUP
# -----------------------------

sudo mkdir -p /etc/wireguard

wg genkey | sudo tee /etc/wireguard/server_private.key | wg pubkey | sudo tee /etc/wireguard/server_public.key

SERVER_PRIVATE_KEY=$(sudo cat /etc/wireguard/server_private.key)

cat <<EOF | sudo tee /etc/wireguard/wg0.conf

[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = $SERVER_PRIVATE_KEY

PostUp = ufw route allow in on wg0 out on eth0
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

PostDown = ufw route delete allow in on wg0 out on eth0
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

EOF

# -----------------------------
# ENABLE IP FORWARDING
# -----------------------------

sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf

sudo sysctl -p

# -----------------------------
# START WIREGUARD
# -----------------------------

sudo systemctl enable wg-quick@wg0

sudo systemctl start wg-quick@wg0

# -----------------------------
# FINAL OUTPUT
# -----------------------------

echo "======================================="
echo " SERVER SETUP COMPLETE "
echo "======================================="

echo "SSH Port: $SSH_PORT"
echo "Admin User: $ADMIN_USER"

echo ""
echo "WireGuard Public Key:"
sudo cat /etc/wireguard/server_public.key