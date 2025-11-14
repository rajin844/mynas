// lib/pages/dashboard_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/monitoring_provider.dart';
import '../providers/zfs_provider.dart';
import '../providers/shares_provider.dart';
import '../services/websocket_service.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  @override
  void initState() {
    super.initState();

    final ws = context.read<WebSocketService>();
    // final monitor = context.read<MonitoringProvider>();
    final zfs = context.read<ZfsProvider>();
    final shares = context.read<SharesProvider>();

    // initial loads
    Future.microtask(() async {
      //await monitor.refresh();
      await zfs.loadPools();
      await shares.loadShares();
    });

    //if (msg['module'] == 'zfs') {
    //     monitor.addEvent("monitor: ${msg.toString()}");
    // } else

    ws.stream.listen((msg) {
      if (!mounted) return;
      if (msg is Map) {
        if (msg['module'] == 'zfs') {
          zfs.loadPools();
        } else if (msg['module'] == 'shares') {
          shares.loadShares();
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final monitor = context.watch<MonitoringProvider>();
    final ws = context.watch<WebSocketService>();

    return Scaffold(
      appBar: AppBar(title: const Text('MyNAS Dashboard')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(children: [
              Chip(
                avatar: Icon(ws.connected ? Icons.check_circle : Icons.error),
                label: Text(ws.connected ? "Connected" : "Disconnected"),
                backgroundColor:
                    ws.connected ? Colors.green[50] : Colors.red[50],
              ),
              const SizedBox(width: 16),
              ElevatedButton(
                onPressed: () => context.read<MonitoringProvider>().refresh(),
                child: const Text('Refresh metrics'),
              ),
            ]),
            const SizedBox(height: 14),
            Row(
              children: [
                _metricCard('CPU', '${monitor.cpu}%'),
                const SizedBox(width: 12),
                _metricCard('RAM', '${monitor.ram}%'),
                const SizedBox(width: 12),
                _metricCard('Disk', '${monitor.disk}%'),
              ],
            ),
            const SizedBox(height: 20),
            Expanded(
              child: ListView(
                children: monitor.events
                    .map((e) => ListTile(title: Text(e)))
                    .toList(),
              ),
            )
          ],
        ),
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            const DrawerHeader(child: Text('MyNAS')),
            ListTile(
              leading: const Icon(Icons.dashboard),
              title: const Text('Dashboard'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              leading: const Icon(Icons.storage),
              title: const Text('Pools'),
              onTap: () {
                Navigator.pop(context);
                Navigator.pushNamed(context, '/pools');
              },
            ),
            ListTile(
              leading: const Icon(Icons.folder),
              title: const Text('Datasets'),
              onTap: () {
                Navigator.pop(context);
                Navigator.pushNamed(context, '/datasets');
              },
            ),
            ListTile(
              leading: const Icon(Icons.share),
              title: const Text('Shares'),
              onTap: () {
                Navigator.pop(context);
                Navigator.pushNamed(context, '/shares');
              },
            ),
            ListTile(
              leading: const Icon(Icons.backup),
              title: const Text('Backups'),
              onTap: () {
                Navigator.pop(context);
                Navigator.pushNamed(context, '/backup');
              },
            ),
            ListTile(
              leading: const Icon(Icons.settings),
              title: const Text('Settings'),
              onTap: () {
                Navigator.pop(context);
                Navigator.pushNamed(context, '/settings');
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _metricCard(String title, String value) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            children: [
              Text(title),
              const SizedBox(height: 8),
              Text(value,
                  style: const TextStyle(
                      fontSize: 22, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
      ),
    );
  }
}
