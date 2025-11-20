import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:frontend_flutter/providers/storage_provider.dart';
import 'package:frontend_flutter/widgets/drawer.dart';
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
    final monitor = context.read<MonitoringProvider>();
    final zfs = context.read<ZfsProvider>();
    final shares = context.read<SharesProvider>();
    final storage = context.read<StorageProvider>();

    Future.microtask(() async {
      await monitor.refresh();
      await zfs.loadPools();
      await shares.loadShares();
    });

    ws.stream.listen((raw) {
      if (!mounted) return;

      dynamic msg;
      try {
        msg = jsonDecode(raw);
      } catch (e) {
        debugPrint("WS decode error: $e");
        return;
      }

      if (msg is Map && msg['module'] == 'monitor') {
        monitor.updateFromWs(msg['data']);
      } else if (msg is Map && msg['module'] == 'zfs') {
        zfs.loadPools();
      } else if (msg is Map && msg['module'] == 'storage') {
        storage.loadSummary();
      } else if (msg is Map && msg['module'] == 'shares') {
        shares.loadShares();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final monitor = context.watch<MonitoringProvider>();
    final storage = context.watch<StorageProvider>();
    final zfs = context.watch<ZfsProvider>();
    final ws = context.watch<WebSocketService>();

    return Scaffold(
      appBar: AppBar(title: const Text("MyNAS Dashboard")),
      drawer: AppDrawer(
        onSelect: (route) {
          Navigator.pop(context);
          Navigator.pushNamed(context, route);
        },
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          // CONNECTION + REFRESH
          Row(children: [
            Chip(
                avatar: Icon(ws.connected ? Icons.check_circle : Icons.error,
                    color: ws.connected ? Colors.green : Colors.red),
                label: Text(ws.connected ? "Connected" : "Disconnected")),
            const SizedBox(width: 16),
            ElevatedButton(
                onPressed: () => monitor.refresh(),
                child: const Text("Refresh Metrics"))
          ]),

          const SizedBox(height: 16),

          // MONITORING METRICS
          Row(children: [
            _metricCard("CPU", "${monitor.cpu.toStringAsFixed(1)}%"),
            const SizedBox(width: 12),
            _metricCard("RAM", "${monitor.ram.toStringAsFixed(1)}%"),
            const SizedBox(width: 12),
            _metricCard("Disk", "${monitor.disk.toStringAsFixed(1)}%"),
          ]),

          const SizedBox(height: 20),

          // -------------------------------
          // STORAGE SUMMARY TILE
          // -------------------------------
          _storageSummaryTile(storage),

          const SizedBox(height: 15),

          // -------------------------------
          // OVERVIEW WIDGETS (Storage + Pools)
          // -------------------------------
          Expanded(
            child: Row(
              children: [
                Expanded(child: _storageOverview(storage)),
                const SizedBox(width: 12),
                Expanded(child: _poolsOverviewWidget(zfs)),
              ],
            ),
          )
        ]),
      ),
    );
  }

  // ------------------------- Drawer -------------------------

  // ------------------------- Widgets -------------------------
  Widget _metricCard(String label, String value) {
    return Expanded(
      child: Card(
        elevation: 1,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              Text(label),
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

  // STORAGE SUMMARY TILE
  Widget _storageSummaryTile(StorageProvider storage) {
    final s = storage.summary ?? {};

    return Card(
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(children: [
          _miniStat("Disks", s["disks"] ?? 0),
          const SizedBox(width: 20),
          _miniStat("Pools", s["pools"] ?? 0),
          const SizedBox(width: 20),
          _miniStat("Datasets", s["datasets"] ?? 0),
        ]),
      ),
    );
  }

  Widget _miniStat(String label, int value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
        const SizedBox(height: 4),
        Text(
          value.toString(),
          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
        ),
      ],
    );
  }

  // STORAGE OVERVIEW
  // ------------------ STORAGE OVERVIEW ------------------
  Widget _storageOverview(StorageProvider storage) {
    return Card(
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Storage Overview",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const Divider(),
            Text("Total Disks: ${storage.summary?["disks"] ?? 0}"),
            Text("Total Pools: ${storage.summary?["pools"] ?? 0}"),
            Text("Total Datasets: ${storage.summary?["datasets"] ?? 0}"),
          ],
        ),
      ),
    );
  }

  // POOLS OVERVIEW
  Widget _poolsOverviewWidget(ZfsProvider zfs) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Pools Overview",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const Divider(),
            Expanded(
              child: ListView.builder(
                itemCount: zfs.pools.length,
                itemBuilder: (context, i) {
                  final p = zfs.pools[i];
                  return ListTile(
                    leading: const Icon(Icons.storage),
                    title: Text(p["name"]),
                    subtitle: Text("Health: ${p["health"]}"),
                  );
                },
              ),
            )
          ],
        ),
      ),
    );
  }
}
