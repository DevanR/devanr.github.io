---
layout: post
title: "Setting Up qBittorrent with VPN Integration on Ubuntu Server"
excerpt: ""
categories: articles
tags: [qbittorrent, ubuntu, vpn, jellyfin, media-server]
share: true
comments: false
modified:
---

# Setting Up qBittorrent with VPN Integration on Ubuntu Server

Setting up a torrent client on your home server can significantly enhance your media server setup, allowing you to automate downloads directly to your media library. This guide will walk you through setting up qBittorrent with VPN integration on an Ubuntu server, with specific focus on making it work with Jellyfin.

## Why qBittorrent?

After trying multiple solutions including Transmission, I settled on qBittorrent for its reliability, feature-rich web interface, and better stability. While Transmission is often recommended for its lightweight nature, I encountered numerous stability issues where the daemon would randomly crash or hang.

## Prerequisites

- Ubuntu server (this guide was tested on Ubuntu 24.04 LTS)
- An active VPN subscription (I use ExpressVPN)
- Basic familiarity with Linux command line
- SSH access to your server

## Installation Process

### 1. Install qBittorrent-nox (CLI version with WebUI)

```bash
sudo apt update
sudo apt install qbittorrent-nox
```

### 2. Set Up a Service for qBittorrent

Create a systemd service file to manage qBittorrent:

```bash
sudo nano /etc/systemd/system/qbittorrent.service
```

Add the following content, replacing "yourusername" with your actual username:

```
[Unit]
Description=qBittorrent Daemon Service
After=network.target

[Service]
Type=simple
User=yourusername
Group=yourusername
ExecStart=/usr/bin/qbittorrent-nox --webui-port=8080
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### 3. Create Download Directories

```bash
mkdir -p ~/downloads
mkdir -p ~/downloads/incomplete
```

### 4. Configure VPN Integration

#### Install OpenVPN

```bash
sudo apt install openvpn
```

#### Set Up Your VPN Configuration

1. Obtain your OpenVPN configuration files from your VPN provider
2. Create a directory for your VPN configurations:

```bash
sudo mkdir -p /etc/openvpn/vpnprovider
```

3. Upload your .ovpn file to this directory
4. Create a credentials file:

```bash
sudo nano /etc/openvpn/vpnprovider/credentials
```

Add your VPN username on the first line and password on the second.

5. Set secure permissions:

```bash
sudo chmod 600 /etc/openvpn/vpnprovider/credentials
```

#### Create a VPN Service

```bash
sudo nano /etc/systemd/system/vpn.service
```

Add:

```
[Unit]
Description=VPN Connection
After=network.target

[Service]
ExecStart=/usr/sbin/openvpn --config /etc/openvpn/vpnprovider/your-chosen-server.ovpn --auth-user-pass /etc/openvpn/vpnprovider/credentials
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### 5. Link qBittorrent to Your VPN

Update the qBittorrent service file to depend on the VPN:

```bash
sudo nano /etc/systemd/system/qbittorrent.service
```

Modify the [Unit] section:

```
[Unit]
Description=qBittorrent Daemon Service
After=network.target vpn.service
Requires=vpn.service
```

### 6. Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable vpn
sudo systemctl enable qbittorrent
sudo systemctl start vpn
sudo systemctl start qbittorrent
```

## Common Gotchas and Troubleshooting

### The "nonexistent" Home Directory Error

If you see an error like:

```
Could not create required directory '/nonexistent/.cache/qBittorrent'
Aborted
```

This means the user running qBittorrent has an invalid home directory.

**Solution**: Modify your service file to use your actual user account rather than a system user.

### Permission Issues with Download Directories

If Jellyfin can't access your downloaded media:

```bash
# Add the jellyfin user to your group
sudo usermod -a -G yourusername jellyfin

# Ensure your directories have appropriate permissions
chmod 750 ~/downloads
chmod 750 ~/downloads/incomplete
chmod 750 ~/  # May be necessary if jellyfin needs to traverse your home dir

# Restart jellyfin
sudo systemctl restart jellyfin
```

### VPN Connection Dropping

If the VPN connection drops, qBittorrent may continue running but expose your real IP address.

**Solution**: Bind qBittorrent specifically to the VPN interface by adding the `--net-interface=tun0` option:

```bash
ExecStart=/usr/bin/qbittorrent-nox --webui-port=8080 --net-interface=tun0
```

### Web UI Password Reset

If you forget your Web UI password:

1. Stop the service:
```bash
sudo systemctl stop qbittorrent
```

2. Edit the config file:
```bash
nano ~/.config/qBittorrent/qBittorrent.conf
```

3. Find the WebUI section and remove or modify the password line:
```
[WebUI]
Password=
Username=admin
```

4. Restart the service:
```bash
sudo systemctl start qbittorrent
```

### Verifying Your Torrent Traffic Is Using the VPN

Run this command to check:

```bash
sudo ss -tpn | grep qbittorrent
```

Make sure connections show your VPN's private IP (often starting with 10.x.x.x) rather than your actual network interface IP.

## Configuring qBittorrent for Best Performance

Access the Web UI at `http://your-server-ip:8080` (default credentials: admin/adminadmin)

Important settings to adjust:

1. **Downloads**
   - Set "Default Save Path" to your media directory
   - Set proper incomplete download location

2. **Connection**
   - Bind to the VPN interface (tun0)
   - Adjust maximum connections based on your server capacity

3. **Speed**
   - Set upload/download limits to avoid affecting other network activities

4. **BitTorrent**
   - Enable encryption
   - Configure port forwarding if supported by your VPN

## Integrating with Jellyfin

For optimal integration with Jellyfin:

1. Configure qBittorrent to download to directories that Jellyfin scans
2. Ensure proper permissions as outlined in the troubleshooting section
3. Consider setting up auto-categorization based on media type (TV shows vs. Movies)

## Security Considerations

1. Change the default Web UI password immediately
2. Use a VPN that doesn't keep logs
3. Consider implementing additional firewall rules
4. Regularly update your system and qBittorrent

## Conclusion

While setting up qBittorrent with VPN integration requires some initial effort, the result is a robust, secure downloading solution that integrates perfectly with media servers like Jellyfin. The combination of automated downloads and proper VPN protection makes for an excellent self-hosted solution that puts you in control of your media library.
