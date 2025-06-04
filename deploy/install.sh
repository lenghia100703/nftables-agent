#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CURRENT_USER=$SUDO_USER

echo "Installing required packages..."
apt update
apt install -y python3-venv supervisor

echo "Creating virtual environment..."
cd "$PROJECT_DIR"
python3 -m venv venv
VENV_PATH="$PROJECT_DIR/venv"

echo "Installing Python dependencies..."
$VENV_PATH/bin/pip install -r requirements.txt

echo "Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please edit .env file with your configuration"
    read -p "Press enter to continue..."
fi

mkdir -p /var/log/nftables_agent
chown $CURRENT_USER:$CURRENT_USER /var/log/nftables_agent

echo "Configuring supervisor..."
SUPERVISOR_CONF="/etc/supervisor/conf.d/nftables_agent.conf"
cp deploy/supervisor/nftables_agent.conf $SUPERVISOR_CONF

sed -i "s|%(ENV_PROJECT_PATH)s|$PROJECT_DIR|g" $SUPERVISOR_CONF
sed -i "s|%(ENV_VENV_PATH)s|$VENV_PATH|g" $SUPERVISOR_CONF
sed -i "s|%(ENV_USER)s|$CURRENT_USER|g" $SUPERVISOR_CONF

while IFS='=' read -r key value
do
    if [ ! -z "$key" ]; then
        sed -i "s|%(ENV_${key})s|${value}|g" $SUPERVISOR_CONF
    fi
done < .env

echo "Restarting supervisor..."
supervisorctl reread
supervisorctl update
supervisorctl restart nftables_agent

echo "Installation completed!"
echo "You can check the service status with: sudo supervisorctl status nftables_agent"
echo "Logs are available in /var/log/nftables_agent/"