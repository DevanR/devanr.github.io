---
layout: post
title: "Setting Up a ProxMox Server with Immich and a Removable SATA Drive"
excerpt: ""
categories: articles
tags: [proxmox, immich]
tags: dell poweredge r410 raid proxmox immich docker
share: true
comments: false
modified:
---

# Setting Up a ProxMox Server with Immich and a Removable SATA Drive

In this guide, I'll walk through the complete process of setting up a Dell PowerEdge R410 as a ProxMox server with a removable SATA drive for a self-hosted Immich photo and video backup solution. This setup allows me to easily remove and back up the media disk whenever needed.

## Project Overview

Here's what we set out to accomplish:

1. Set up and configure a used Dell PowerEdge R410 as a ProxMox virtualization server
2. Configure the first 3 SAS disks as RAID-0 for ProxMox OS and VM storage
3. Configure the 4th SATA disk as an external media disk to be used by Immich
4. Install and configure an Ubuntu Server VM to run Immich
5. Make the media disk removable for easy backup

## Hardware Setup

### Server Configuration
- Dell PowerEdge R410
- 3x SAS drives in RAID-0 for the main system
- 1x SATA 4TB drive as a removable media disk
- PERC H700 RAID controller

## Part 1: Initial ProxMox Setup

### Preparing the Installation Media with Ventoy

I used Ventoy to create the bootable USB drive for ProxMox installation. Ventoy is an open-source tool that allows you to create a bootable USB drive where you can simply copy multiple ISO files to the drive and boot from any of them without needing to reformat the drive each time.

Here's how I set it up:
1. Download and install Ventoy on a USB drive:
   - Use VirtualBox and boot into a Linux live environment
   - Connect USB drive and install Ventoy to it
   - Download the ProxMox ISO and copy it to the Ventoy USB drive
   - Ventoy automatically creates a boot menu with all ISOs on the drive

2. Boot the server with the USB drive and prepare the RAID configuration:
   - Press **CTRL+R** during boot to access the RAID configuration utility
   - Use **F10** to configure BIOS settings as needed
   - Create a new Virtual Disk (VD) for the 3 SAS disks (RAID-0)
   - Create a new Virtual Disk (VD) for the 4th media disk (RAID-0)

> **Important:** Wait for the new VD to be fully initialized before attempting OS installation!

### Installation Gotchas

I encountered several issues during installation:

- **Tip:** You might need to remove the 4th disk for the installation to work properly
- **Alternative approach:** If installation fails, remove the 4th drive during installation of ProxMox, then set up ProxMox with the VM. After that, reboot the machine with the 4th disk attached and create a new VD for it.

I installed ProxMox on the RAID-0 array of the three SAS disks. After the basic installation, I had to deal with repository configuration.

### Fixing Enterprise Repository Issues

After installation, I needed to switch from the enterprise repositories to the free community repositories:

1. Edit the enterprise repository file:
   ```bash
   nano /etc/apt/sources.list.d/pve-enterprise.list
   ```

2. Comment out the enterprise repository by adding a # at the beginning of the line:
   ```bash
   # deb https://enterprise.proxmox.com/debian/pve bookworm pve-enterprise
   ```

3. Add the no-subscription repository:
   ```bash
   echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" > /etc/apt/sources.list.d/pve-no-subscription.list
   ```

4. Similarly for Ceph, edit its repository file:
   ```bash
   nano /etc/apt/sources.list.d/ceph.list
   ```

5. Comment out the enterprise repository and add the no-subscription one:
   ```bash
   # deb https://enterprise.proxmox.com/debian/ceph-quincy bookworm enterprise
   deb http://download.proxmox.com/debian/ceph-quincy bookworm no-subscription
   ```

6. Update the package lists:
   ```bash
   apt update
   ```

This allowed me to receive updates without requiring a subscription.

## Part 2: Configuring the SATA Disk

Initially, the 4th SATA disk wasn't being detected properly. After some troubleshooting, I discovered it was showing up as a "Foreign Configuration" in the PERC H700 RAID controller.

### Resolving Foreign Configuration

To resolve this, I accessed the PERC H700 BIOS during system boot by pressing Ctrl+R and found the disk listed as a foreign configuration. Since I wanted to use it as a standalone disk rather than part of an existing array, I cleared the foreign configuration:

1. In the PERC H700 BIOS, selected "Foreign Config" > "Clear"
2. This made the disk available as an unconfigured good disk
3. Created a new single-disk RAID-0 virtual disk with that physical disk

### Repairing the GPT Partition Table

After adding the disk to ProxMox, I discovered the disk had a corrupted GPT partition table. I used `gdisk` to fix it:

```bash
gdisk -l /dev/sdb
```

This showed several problems with the GPT partition table:

```
Caution: Found protective or hybrid MBR and corrupt GPT. Using GPT, but disk
verification and recovery are STRONGLY recommended.
```

I entered recovery mode and accessed the expert menu to fix the issues:

```bash
# In gdisk
Command (? for help): r
Recovery/transformation command (? for help): x
Expert command (? for help): e
```

This relocated the backup data structures to the end of the disk. After verification, I wrote the changes with the `w` command.

### Creating a New Partition and Filesystem

Since I wanted to use this as a fresh disk for Immich, I created a new partition table and formatted it with ext4:

```bash
# Create a new empty GPT partition table
gdisk /dev/sdb
# Type 'o' for new table
# Type 'n' for new partition
# Accept defaults for first and last sectors
# Type '0700' for basic data partition
# Type 'w' to write changes

# Format with ext4 (not exFAT as initially planned)
mkfs.ext4 /dev/sdb
```

I initially planned to use exFAT for better cross-platform compatibility, but ultimately went with ext4 as it's the native Linux filesystem with better performance, journaling for improved data integrity, and is fully supported by default in Linux systems.

## Part 3: Adding the Disk to ProxMox

Once the disk was prepared, I needed to make it accessible to ProxMox:

```bash
# Check the UUID of the disk
blkid /dev/sdb1
# Output: UUID="E7E6-D94B" BLOCK_SIZE="512" TYPE="exfat" PTTYPE="dos" PARTLABEL="Microsoft basic data" PARTUUID="88025e98-0e04-49da-b48d-0ad992798361"
```

## Part 4: Setting Up the Ubuntu VM for Immich

I created an Ubuntu Server VM in ProxMox with the following specifications:
- 4GB RAM
- 6 CPU cores
- 80GB main disk

### Attaching the Media Disk to the VM

I used the command line to attach the formatted disk to the VM:

```bash
# Get the VM ID
qm list
# Output showed VM ID 100 for Immich VM

# Attach the disk to the VM
qm set 100 -scsi1 /dev/sdb1
```

You can verify the disk was added to the VM configuration:

```bash
qm config 100
```

The output should show something like:
```
scsi1: /dev/sdb1,size=4000224099840
```

## Part 5: Configuring the VM to Use the External Disk

After starting the VM, I needed to mount the disk and make it available to Immich.

### Installing exFAT Support in the VM

First, I installed exFAT support in the Ubuntu VM:

```bash
sudo apt update
sudo apt install exfat-fuse exfat-utils
```

### Creating a Mount Point and Mounting the Disk

```bash
# Create mount point
sudo mkdir -p /mnt/immich-media

# Mount the disk
sudo mount /dev/sdb /mnt/immich-media

# Verify the mount
df -h | grep immich-media
```

### Making the Mount Persistent

To ensure the disk is mounted automatically on boot, I added it to `/etc/fstab`:

```bash
echo "/dev/sdb /mnt/immich-media ext4 defaults,nofail 0 0" | sudo tee -a /etc/fstab
```

The `nofail` option ensures the system boots normally even if the disk is not present.

## Part 6: Setting Up Immich with Docker Compose

I installed Immich using the official Docker Compose setup, then modified it to use the external disk.

### Configuring Docker Compose for the External Disk

For the Immich setup, I decided to keep the default upload location while still making the external disk available to the container. I edited the docker-compose.yml file to add the external media volume:

```yaml
volumes:
  - ${UPLOAD_LOCATION}:/usr/src/app/upload
  - /mnt/immich-media:/usr/src/app/external-media
```

This approach maintains the default `/usr/src/app/upload` path for the primary library storage while making the external disk available as an additional location. This provides more flexibility for managing media content and allows the default library structure to remain intact.

I could have alternatively modified the `.env` file to change the `UPLOAD_LOCATION` variable, but I found keeping the default structure more maintainable.

### Setting Up Auto-Start for Docker Compose

Since Docker was installed via Snap on my system, I created a systemd service to ensure Immich starts automatically on boot:

```bash
sudo nano /etc/systemd/system/immich.service
```

With the following content:

```ini
[Unit]
Description=Immich Docker Compose Application
After=snapd.service network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/your/immich/directory
ExecStartPre=/bin/bash -c 'if ! mountpoint -q /mnt/immich-media; then mount /mnt/immich-media; fi'
ExecStart=/snap/bin/docker-compose up
ExecStop=/snap/bin/docker-compose down
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enabled and started the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable immich.service
sudo systemctl start immich.service
```

## Part 7: Configuring Immich to Use the External Media

Finally, I configured Immich through its web interface to use the external media directory:

1. Logged into the Immich web interface
2. Went to Administration → Library Settings
3. Configured the external media path as the primary upload destination

## Conclusion

This setup provides a flexible solution for a self-hosted photo and video backup system using Immich on ProxMox. The key advantage is the ability to remove the media disk for offline backups while maintaining a clean separation between the system and media storage.

When I need to back up my media or add content from another system:

1. Shut down the Immich containers
2. Unmount the disk: `sudo umount /mnt/immich-media`
3. Shut down the VM
4. Detach the disk from the VM in ProxMox
5. Physically remove the disk from the server

To reconnect:
1. Physically install the disk
2. Reattach it to the VM in ProxMox
3. Start the VM, and the disk will be automatically mounted
4. The Immich service will start automatically

This modular approach offers both the convenience of a self-hosted solution with the practical ability to physically secure or transport the actual media data when needed.

## Troubleshooting Tips

- If the disk doesn't mount automatically after a reboot, check `/etc/fstab` and ensure the entry is correct
- If Docker containers don't start automatically, check the systemd service status with `systemctl status immich.service`
- If you need to repair the disk's filesystem after unexpected removal, you might need to use `fsck.exfat /dev/sdb1`

## Future Improvements

- Implement a more robust backup solution like rsync to an additional backup disk
- Set up email notifications when the disk space reaches a certain threshold
- Add monitoring for the health of the RAID arrays and the media disk
