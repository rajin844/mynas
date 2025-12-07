// lib/widgets/app_drawer.dart
import 'package:flutter/material.dart';

typedef OnSelectRoute = void Function(String route);

class AppDrawer extends StatelessWidget {
  final OnSelectRoute onSelect;
  final String? currentRoute;
  final Map<String, int>? counts;
  final String? username;
  final String? hostname;
  final String? version;

  const AppDrawer({
    super.key,
    required this.onSelect,
    this.currentRoute,
    this.counts,
    this.username,
    this.hostname,
    this.version,
  });

  // Helper to build a tile; shows optional badge if counts contains routeKey
  Widget _tile(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String route,
    String? subtitle,
    Color? iconColor,
    bool selected = false,
    bool dense = false,
  }) {
    final count = counts != null ? counts![route] : null;

    return ListTile(
      dense: dense,
      leading:
          Icon(icon, color: iconColor ?? Theme.of(context).iconTheme.color),
      title: Text(title),
      subtitle: subtitle != null ? Text(subtitle) : null,
      trailing: count != null
          ? CircleAvatar(
              radius: 12,
              backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
              child: Text(
                count.toString(),
                style: TextStyle(
                    fontSize: 12,
                    color: Theme.of(context).colorScheme.onSecondaryContainer),
              ),
            )
          : null,
      selected: selected,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      onTap: () => onSelect(route),
    );
  }

  Widget _sectionHeader(String text) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
      child: Text(
        text.toUpperCase(),
        style: const TextStyle(
            fontSize: 12, color: Colors.grey, fontWeight: FontWeight.w600),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final primary = theme.colorScheme.primary;

    return Drawer(
      child: SafeArea(
        child: Column(
          children: [
            _buildHeader(context),
            Expanded(
              child: Scrollbar(
                child: ListView(
                  padding: EdgeInsets.zero,
                  children: [
                    // MAIN
                    _sectionHeader("Main"),
                    _tile(
                      context,
                      icon: Icons.dashboard,
                      title: "Dashboard",
                      route: '/dashboard',
                      selected: currentRoute == '/dashboard',
                    ),

                    // STORAGE group
                    _sectionHeader("Storage"),
                    ExpansionTile(
                      initiallyExpanded:
                          currentRoute?.startsWith('/storage') ?? false,
                      leading: Icon(Icons.storage_rounded),
                      title: const Text("Storage"),
                      childrenPadding:
                          const EdgeInsets.only(left: 12, right: 12, bottom: 8),
                      children: [
                        _tile(
                          context,
                          icon: Icons.storage,
                          title: "Disks",
                          route: '/storage',
                          dense: true,
                          selected: currentRoute == '/storage',
                        ),
                        // _tile(
                        // context,
                        //icon: Icons.sd_storage_outlined,
                        //title: "Pools",
                        //route: '/pools',
                        //dense: true,
                        //selected: currentRoute == '/pools',
                        //iconColor: Colors.teal,
                        //),
                        _tile(
                          context,
                          icon: Icons.sd_storage_outlined,
                          title: "Pools",
                          route: '/pools',
                          dense: true,
                          selected: currentRoute == '/pools',
                          iconColor: Colors.teal,
                        ),
                        _tile(
                          context,
                          icon: Icons.sd_storage_outlined,
                          title: "PoolDetailspage",
                          route: '/pooldetailspage',
                          dense: true,
                          selected: currentRoute == '/pooldetailspage',
                          iconColor: Colors.teal,
                        ),
                        _tile(
                          context,
                          icon: Icons.dataset,
                          title: "Datasets",
                          route: '/datasets',
                          dense: true,
                          selected: currentRoute == '/datasets',
                        ),
                        _tile(
                          context,
                          icon: Icons.settings_suggest,
                          title: "ZFS Manager",
                          route: '/zfsmanager',
                          dense: true,
                          selected: currentRoute == '/zfsmanager',
                        ),
                      ],
                    ),

                    // SHARING group
                    _sectionHeader("Sharing"),
                    ExpansionTile(
                      initiallyExpanded:
                          currentRoute?.startsWith('/shares') ?? false,
                      leading: const Icon(Icons.folder_shared),
                      title: const Text("Shares"),
                      childrenPadding:
                          const EdgeInsets.only(left: 12, right: 12, bottom: 8),
                      children: [
                        _tile(
                          context,
                          icon: Icons.folder,
                          title: "SMB/NFS Shares",
                          route: '/shares',
                          dense: true,
                          selected: currentRoute == '/shares',
                        ),
                        _tile(
                          context,
                          icon: Icons.backup,
                          title: "Snapshot / Backup",
                          route: '/backup',
                          dense: true,
                          selected: currentRoute == '/backup',
                        ),
                      ],
                    ),

                    // SYSTEM group
                    _sectionHeader("System"),
                    ExpansionTile(
                      initiallyExpanded:
                          currentRoute?.startsWith('/system') ?? false,
                      leading: const Icon(Icons.settings),
                      title: const Text("System"),
                      childrenPadding:
                          const EdgeInsets.only(left: 12, right: 12, bottom: 8),
                      children: [
                        _tile(
                          context,
                          icon: Icons.person,
                          title: "Users",
                          route: '/users',
                          dense: true,
                          selected: currentRoute == '/users',
                        ),
                        _tile(
                          context,
                          icon: Icons.lock,
                          title: "ACL",
                          route: '/acl',
                          dense: true,
                          selected: currentRoute == '/acl',
                        ),
                        _tile(
                          context,
                          icon: Icons.network_check,
                          title: "Network",
                          route: '/network',
                          dense: true,
                          selected: currentRoute == '/network',
                        ),
                        _tile(
                          context,
                          icon: Icons.settings_suggest,
                          title: "System Settings",
                          route: '/system',
                          dense: true,
                          selected: currentRoute == '/settings',
                        ),
                      ],
                    ),

                    // ADVANCED group
                    _sectionHeader("Advanced"),
                    ExpansionTile(
                      initiallyExpanded:
                          currentRoute?.startsWith('/advanced') ?? false,
                      leading: const Icon(Icons.build),
                      title: const Text("Advanced"),
                      childrenPadding:
                          const EdgeInsets.only(left: 12, right: 12, bottom: 8),
                      children: [
                        _tile(
                          context,
                          icon: Icons.monitor,
                          title: "Monitoring",
                          route: '/monitoring',
                          dense: true,
                          selected: currentRoute == '/monitoring',
                        ),
                        _tile(
                          context,
                          icon: Icons.backup,
                          title: "Backups",
                          route: '/backup',
                          dense: true,
                          selected: currentRoute == '/backup',
                        ),
                        _tile(
                          context,
                          icon: Icons.bug_report,
                          title: "System Logs",
                          route: '/logs',
                          dense: true,
                          selected: currentRoute == '/logs',
                        ),
                        _tile(
                          context,
                          icon: Icons.developer_mode,
                          title: "Developer Tools",
                          route: '/developer',
                          dense: true,
                          selected: currentRoute == '/developer',
                        ),
                      ],
                    ),

                    const SizedBox(height: 12),
                  ],
                ),
              ),
            ),

            // footer - small info and sign out
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Column(
                children: [
                  const Divider(),
                  ListTile(
                    dense: true,
                    leading: const Icon(Icons.info_outline),
                    title: Text(hostname ?? "mynas"),
                    subtitle: Text("v${version ?? "1.0.0"}"),
                    onTap: () {},
                  ),
                  ListTile(
                    dense: true,
                    leading: const Icon(Icons.logout),
                    title: const Text("Sign out"),
                    onTap: () => onSelect('/logout'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    final avatar = CircleAvatar(
      radius: 28,
      backgroundColor: Theme.of(context).colorScheme.primaryContainer,
      child: Text(
        username != null && username!.isNotEmpty
            ? username![0].toUpperCase()
            : "A",
        style: const TextStyle(fontSize: 24),
      ),
    );

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      child: Row(
        children: [
          avatar,
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  username ?? "Admin",
                  style: const TextStyle(
                      fontWeight: FontWeight.w700, fontSize: 16),
                ),
                const SizedBox(height: 4),
                Text(
                  hostname ?? "mynas",
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: () => onSelect('/settings'),
            icon: const Icon(Icons.settings),
            tooltip: "Settings",
          )
        ],
      ),
    );
  }
}
