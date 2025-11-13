#!/usr/bin/env python3
"""
CLI frontend for NAS storage management
"""
import os
from storage import storage_manager, zfs_manager, acl_manager, share_manager, network_manager
from system import system_settings

def main_menu():
    print("=== MyNAS Storage Management ===")

    while True:
        print("\nSelect an option:")
        print("1) Detect Disks")
        print("2) List ZFS Pools")
        print("3) Create ZFS Pool")
        print("4) Create Dataset")
        print("5) Assign ACL")
        print("6) Create Samba Share")
        print("7) Create NFS Share")
        print("8) Network Settings")
        print("9) System Settings")
        print("0) Exit")
        choice = input("Choice: ")

        if choice == "1":
            disks = storage_manager.detect_disks()
            print("Detected Disks:")
            for d in disks:
                info = storage_manager.disk_info(d)
                print(info)

        elif choice == "2":
            pools = zfs_manager.list_pools()
            print("ZFS Pools:", pools)

        elif choice == "3":
            pool_name = input("Pool name: ")
            disks = input("Disks (comma-separated, e.g., /dev/sda,/dev/sdb): ").split(",")
            zfs_manager.create_pool(pool_name, disks)

        elif choice == "4":
            pool_name = input("Pool name: ")
            dataset_name = input("Dataset name: ")
            zfs_manager.create_dataset(pool_name, dataset_name)

        elif choice == "5":
            dataset = input("Dataset name: ")
            user = input("User or Group: ")
            permission = input("Permission (read/write/full): ")
            acl_manager.set_acl(dataset, user, permission)

        elif choice == "6":
            dataset = input("Dataset name: ")
            share_name = input("Share name: ")
            share_manager.create_samba_share(dataset, share_name)

        elif choice == "7":
            dataset = input("Dataset name: ")
            share_manager.create_nfs_share(dataset)

        elif choice == "8":
            interfaces = network_manager.list_interfaces()
            print("Network Interfaces:", interfaces)
            iface = input("Select interface to configure: ")
            ip = input("IP address: ")
            gateway = input("Gateway: ")
            dns = input("DNS (optional): ")
            network_manager.set_static_ip(iface, ip, gateway, dns)
            network_manager.restart_network()

        elif choice == "9":
            hostname = input("Set NAS hostname (leave blank to skip): ")
            if hostname:
                system_settings.set_hostname(hostname)
            services = system_settings.list_services()
            print("Current Services Status:", services)
            svc_choice = input("Enable or Disable service (format: enable smbd / disable nfs-server, leave blank to skip): ")
            if svc_choice:
                parts = svc_choice.split()
                if len(parts) == 2:
                    action, svc = parts
                    if action.lower() == "enable":
                        system_settings.enable_service(svc)
                    elif action.lower() == "disable":
                        system_settings.disable_service(svc)

        elif choice == "0":
            print("Exiting CLI...")
            break

        else:
            print("Invalid option!")

if __name__ == "__main__":
    main_menu()
