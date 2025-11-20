import 'package:flutter/material.dart';

class AppDrawer extends StatefulWidget {
  final Function(String) onSelect;

  const AppDrawer({super.key, required this.onSelect});

  @override
  State<AppDrawer> createState() => _AppDrawerState();
}

class _AppDrawerState extends State<AppDrawer> {
  String currentRoute = "/dashboard";

  // Expansion states
  bool storageOpen = false;
  bool sharingOpen = false;
  bool systemOpen = false;
  bool advancedOpen = false;

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: SafeArea(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            // ---------------------------------------------------
            // HEADER
            // ---------------------------------------------------
            DrawerHeader(
              decoration: const BoxDecoration(
                color: Color(0xFF1565C0),
              ),
              child: const Align(
                alignment: Alignment.bottomLeft,
                child: Text(
                  "MyNAS",
                  style: TextStyle(
                    fontSize: 28,
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),

            // ---------------------------------------------------
            // Dashboard (top-level)
            // ---------------------------------------------------
            _navItem(
              icon: Icons.dashboard,
              label: "Dashboard",
              route: "/dashboard",
            ),

            // ---------------------------------------------------
            // STORAGE (Expandable Section)
            // ---------------------------------------------------
            _sectionHeader(
              "Storage",
              storageOpen,
              () => setState(() => storageOpen = !storageOpen),
            ),
            if (storageOpen) ...[
              _navItem(
                icon: Icons.storage_rounded,
                label: "Disks",
                route: "/storage",
                indent: true,
              ),
              _navItem(
                icon: Icons.pool,
                label: "Pools",
                route: "/pools",
                indent: true,
              ),
              _navItem(
                icon: Icons.layers,
                label: "Datasets",
                route: "/datasets",
                indent: true,
              ),
              _navItem(
                icon: Icons.account_tree,
                label: "ZFS Manager",
                route: "/zfs",
                indent: true,
              ),
            ],

            // ---------------------------------------------------
            // SHARING
            // ---------------------------------------------------
            _sectionHeader(
              "Sharing",
              sharingOpen,
              () => setState(() => sharingOpen = !sharingOpen),
            ),
            if (sharingOpen) ...[
              _navItem(
                icon: Icons.share,
                label: "Shares",
                route: "/shares",
                indent: true,
              ),
              _navItem(
                icon: Icons.security,
                label: "ACL Manager",
                route: "/acl",
                indent: true,
              ),
            ],

            // ---------------------------------------------------
            // SYSTEM
            // ---------------------------------------------------
            _sectionHeader(
              "System",
              systemOpen,
              () => setState(() => systemOpen = !systemOpen),
            ),
            if (systemOpen) ...[
              _navItem(
                icon: Icons.network_check,
                label: "Network",
                route: "/network",
                indent: true,
              ),
              _navItem(
                icon: Icons.task,
                label: "Tasks",
                route: "/tasks",
                indent: true,
              ),
              _navItem(
                icon: Icons.group,
                label: "Users & Groups",
                route: "/users",
                indent: true,
              ),
              _navItem(
                icon: Icons.monitor_heart,
                label: "Metrics",
                route: "/monitoring",
                indent: true,
              ),
              _navItem(
                icon: Icons.notifications,
                label: "Alerts & Events",
                route: "/alerts",
                indent: true,
              ),
            ],

            // ---------------------------------------------------
            // ADVANCED
            // ---------------------------------------------------
            _sectionHeader(
              "Advanced",
              advancedOpen,
              () => setState(() => advancedOpen = !advancedOpen),
            ),
            if (advancedOpen) ...[
              _navItem(
                icon: Icons.construction,
                label: "RAIDZ Builder",
                route: "/raidz",
                indent: true,
              ),
              _navItem(
                icon: Icons.engineering,
                label: "Maintenance Tools",
                route: "/maint",
                indent: true,
              ),
            ],

            const Divider(),

            // ---------------------------------------------------
            // SETTINGS
            // ---------------------------------------------------
            _navItem(
              icon: Icons.settings,
              label: "Settings",
              route: "/settings",
            ),
          ],
        ),
      ),
    );
  }

  // ----------------------------------------------------------
  // NAV ITEM (WITH ACTIVE HIGHLIGHT)
  // ----------------------------------------------------------
  Widget _navItem({
    required IconData icon,
    required String label,
    required String route,
    bool indent = false,
  }) {
    final bool active = (route == currentRoute);

    return Material(
      color: active ? Colors.blue.shade50 : Colors.transparent,
      child: ListTile(
        contentPadding: EdgeInsets.only(
          left: indent ? 40 : 20,
          right: 20,
        ),
        leading: Icon(
          icon,
          color: active ? Colors.blue : Colors.black87,
        ),
        title: Text(
          label,
          style: TextStyle(
            fontWeight: active ? FontWeight.bold : FontWeight.normal,
            color: active ? Colors.blue : Colors.black,
          ),
        ),
        onTap: () {
          setState(() => currentRoute = route);
          widget.onSelect(route);
        },
      ),
    );
  }

  // ----------------------------------------------------------
  // EXPANDABLE SECTION HEADER
  // ----------------------------------------------------------
  Widget _sectionHeader(
      String title, bool expanded, VoidCallback toggleExpand) {
    return ListTile(
      title: Text(
        title,
        style: const TextStyle(
            fontSize: 13, fontWeight: FontWeight.bold, color: Colors.grey),
      ),
      trailing: Icon(
        expanded ? Icons.expand_less : Icons.expand_more,
        size: 20,
      ),
      onTap: toggleExpand,
    );
  }
}
