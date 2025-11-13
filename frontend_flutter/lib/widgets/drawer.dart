import 'package:flutter/material.dart';

class AppDrawer extends StatelessWidget {
  final Function(String) onSelect;

  const AppDrawer({super.key, required this.onSelect});

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: ListView(
        children: [
          DrawerHeader(
            decoration: BoxDecoration(color: Colors.blue),
            child: Text("My NAS",
                style: TextStyle(fontSize: 24, color: Colors.white)),
          ),
          ListTile(
            leading: Icon(Icons.dashboard),
            title: Text("Dashboard"),
            onTap: () => onSelect('/dashboard'),
          ),
          ListTile(
            leading: Icon(Icons.storage),
            title: Text("Pools"),
            onTap: () => onSelect('/pools'),
          ),
          ListTile(
            leading: Icon(Icons.dataset),
            title: Text("Datasets"),
            onTap: () => onSelect('/datasets'),
          ),
          ListTile(
            leading: Icon(Icons.folder),
            title: Text("Shares"),
            onTap: () => onSelect('/shares'),
          ),
          ListTile(
            leading: Icon(Icons.lock),
            title: Text("ACL"),
            onTap: () => onSelect('/acl'),
          ),
          ListTile(
            leading: Icon(Icons.backup),
            title: Text("Backup"),
            onTap: () => onSelect('/backup'),
          ),
          ListTile(
            leading: Icon(Icons.network_check),
            title: Text("Network"),
            onTap: () => onSelect('/network'),
          ),
          ListTile(
            leading: Icon(Icons.monitor),
            title: Text("Monitoring"),
            onTap: () => onSelect('/monitoring'),
          ),
        ],
      ),
    );
  }
}
