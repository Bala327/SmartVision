#!/bin/sh
GATEWAY="192.168.137.1"
while true; do
    # Restore route if missing
    route -n | grep -q "^0.0.0.0" || {
        route add default gw $GATEWAY dev usb0 2>/dev/null
        echo "[net] Route restored"
    }
    # Always restore DNS
    echo "nameserver 8.8.8.8" > /tmp/resolv.conf
    # Test connectivity
    ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1 || echo "[net] WARNING: no internet"
    sleep 10
done
