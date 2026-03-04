#!/bin/sh
install_pkg() {
    while true; do
        echo "nameserver 8.8.8.8" > /tmp/resolv.conf
        echo "nameserver 1.1.1.1" >> /tmp/resolv.conf
        ping -c 1 pypi.org > /dev/null 2>&1 && break
        echo "DNS not ready, waiting 2s..."
        sleep 2
    done
    echo "DNS OK, installing $1..."
    pip3 install "$1" --break-system-packages --no-build-isolation && return 0
    return 1
}

install_pkg "aiohttp==3.9.5"
install_pkg "google-genai"
echo "Done!"
python3 -c "from google import genai; print('genai ready')"
