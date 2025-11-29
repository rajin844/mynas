// lib/pages/dashboard_page.dart
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/monitoring_provider.dart';
import '../providers/storage_provider.dart';
import '../providers/zfs_provider.dart';
import '../providers/shares_provider.dart';
import '../services/websocket_service.dart';
import '../widgets/drawer.dart';
import '../widgets/glass_card.dart';
import '../widgets/metric_card.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage>
    with SingleTickerProviderStateMixin {
  late final AnimationController _entranceCtrl;

  @override
  void initState() {
    super.initState();
    _entranceCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    )..forward();

    final ws = context.read<WebSocketService>();
    final monitor = context.read<MonitoringProvider>();
    final storage = context.read<StorageProvider>();
    final pools = context.read<ZfsProvider>();
    final shares = context.read<SharesProvider>();

    Future.microtask(() async {
      try {
        await monitor.refresh();
      } catch (_) {}
      try {
        await storage.loadSummary();
        await storage.loadAlerts();
      } catch (_) {}
      try {
        await pools.loadPools();
        await pools.loadAllDatasets();
      } catch (_) {}
      try {
        await shares.loadShares();
      } catch (_) {}
    });

    ws.stream.listen((msg) {
      if (!mounted) return;
      if (msg is Map) {
        final module = msg['module'];
        if (module == 'monitor') {
          monitor.updateFromWs(msg);
        } else if (module == 'storage') {
          storage.loadSummary();
          storage.loadAlerts();
        } else if (module == 'zfs') {
          pools.loadPools();
        } else if (module == 'shares') {
          shares.loadShares();
        }
      }
    });
  }

  @override
  void dispose() {
    _entranceCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final monitor = context.watch<MonitoringProvider>();
    final storage = context.watch<StorageProvider>();
    final pools = context.watch<ZfsProvider>();
    final shares = context.watch<SharesProvider>();
    final ws = context.watch<WebSocketService>();

    final theme = Theme.of(context);
    final width = MediaQuery.of(context).size.width;
    final clustered = width >= 1200;

    return Scaffold(
      backgroundColor: const Color(0xFF0B1020),
      appBar: AppBar(
        title: const Text('MyNAS — Dashboard'),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.transparent,
        foregroundColor: Colors.white,
      ),
      drawer: AppDrawer(
        onSelect: (route) {
          Navigator.pop(context);
          Navigator.pushNamed(context, route);
        },
        currentRoute: ModalRoute.of(context)?.settings.name,
        counts: {
          '/pools': pools.pools.length,
          '/storage': (storage.summary['disks'] as List?)?.length ?? 0,
          '/datasets': pools.datasets.length,
          '/shares': shares.shares.length,
        },
        username: 'admin',
        hostname: 'mynas',
        version: '1.0.0',
      ),
      body: FadeTransition(
        opacity: CurvedAnimation(parent: _entranceCtrl, curve: Curves.easeIn),
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
          child: Column(
            children: [
              _buildTopRow(ws, monitor, storage),
              const SizedBox(height: 18),
              _buildAlertRow(storage),
              const SizedBox(height: 18),
              _buildMainGrid(clustered, monitor, storage, pools, shares),
              const SizedBox(height: 28),
            ],
          ),
        ),
      ),
    );
  }

  // Top row: connection + refresh + quick stats
  Widget _buildTopRow(WebSocketService ws, MonitoringProvider monitor,
      StorageProvider storage) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: ws.connected ? Colors.green.shade900 : Colors.red.shade900,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(children: [
            Icon(ws.connected ? Icons.check_circle : Icons.error,
                color: Colors.white, size: 18),
            const SizedBox(width: 8),
            Text(ws.connected ? 'Connected' : 'Disconnected',
                style: const TextStyle(color: Colors.white)),
          ]),
        ),
        const SizedBox(width: 12),
        ElevatedButton.icon(
          onPressed: () async {
            try {
              await monitor.refresh();
            } catch (_) {}
            try {
              await storage.loadSummary();
              await storage.loadAlerts();
            } catch (_) {}
          },
          icon: const Icon(Icons.refresh),
          label: const Text('Refresh'),
          style: ElevatedButton.styleFrom(minimumSize: const Size(120, 40)),
        ),
        const Spacer(),
        _quickStat('CPU', '${monitor.cpu.toStringAsFixed(0)}%'),
        const SizedBox(width: 12),
        _quickStat('RAM', '${monitor.ram.toStringAsFixed(0)}%'),
        const SizedBox(width: 12),
        _quickStat('Disk', '${monitor.disk.toStringAsFixed(0)}%'),
      ],
    );
  }

  Widget _quickStat(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
        const SizedBox(height: 4),
        Text(value,
            style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.white)),
      ],
    );
  }

  // Alerts row — compact TrueNAS-like badges + detailed glass card
  Widget _buildAlertRow(StorageProvider storage) {
    final alerts =
        (storage.alerts is List) ? storage.alerts.cast<dynamic>() : <dynamic>[];
    if (alerts.isEmpty) {
      return Row(
        children: [
          Expanded(
              child: GlassCard(
            title: 'No Active Alerts',
            icon: Icons.check_circle_outline,
            titleColor: Colors.greenAccent,
            child: Padding(
              padding: const EdgeInsets.all(8.0),
              child: Text('System healthy — no storage alerts.',
                  style: TextStyle(color: Colors.green[100])),
            ),
          )),
        ],
      );
    }

    // show small badges then details card
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Wrap(
            spacing: 8,
            children: alerts.take(4).map<Widget>((a) {
              final t = (a is Map) ? (a['type'] ?? 'Alert') : 'Alert';
              final msg = (a is Map) ? (a['message'] ?? '') : a.toString();
              return Tooltip(
                message: msg,
                child: Chip(
                  avatar: const Icon(Icons.warning_amber_rounded,
                      color: Colors.black, size: 18),
                  label: Text(t,
                      style: const TextStyle(fontWeight: FontWeight.bold)),
                  backgroundColor: Colors.redAccent,
                  elevation: 2,
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          flex: 2,
          child: GlassCard(
            title: 'Storage Alerts',
            icon: Icons.warning_amber_rounded,
            titleColor: Colors.redAccent,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: alerts.map<Widget>((a) {
                final t = (a is Map) ? (a['type'] ?? 'Alert') : 'Alert';
                final msg =
                    (a is Map) ? (a['message'] ?? a.toString()) : a.toString();
                return ListTile(
                  dense: true,
                  leading: Icon(Icons.error, color: Colors.redAccent),
                  title: Text(t,
                      style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text(msg),
                );
              }).toList(),
            ),
          ),
        ),
      ],
    );
  }

  // Main responsive grid area
  Widget _buildMainGrid(bool clustered, MonitoringProvider monitor,
      StorageProvider storage, ZfsProvider pools, SharesProvider shares) {
    return LayoutBuilder(builder: (context, constraints) {
      final maxW = constraints.maxWidth;

      if (!clustered) {
        // mobile / narrow layout - vertical stack
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            MetricPanel(monitor: monitor),
            const SizedBox(height: 12),
            _zfsAndStorageStack(storage, pools),
            const SizedBox(height: 12),
            _buildDatasetsOverview(pools),
            const SizedBox(height: 12),
            _buildDisksGrid(storage),
          ],
        );
      }

      // wide layout — grid-like with 3 columns
      return Wrap(
        spacing: 16,
        runSpacing: 16,
        children: [
          SizedBox(
              width: min(maxW * 0.22, 420),
              child: MetricPanel(monitor: monitor)),
          SizedBox(
              width: min(maxW * 0.42, 760),
              child: _buildStorageOverview(storage)),
          SizedBox(
              width: min(maxW * 0.32, 420), child: _buildPoolsOverview(pools)),
          SizedBox(
              width: min(maxW * 0.48, 760),
              child: _buildDatasetsOverview(pools)),
          SizedBox(
              width: min(maxW * 0.48, 760), child: _buildDisksGrid(storage)),
        ],
      );
    });
  }

  Widget _zfsAndStorageStack(StorageProvider storage, ZfsProvider pools) {
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      _buildStorageOverview(storage),
      const SizedBox(height: 12),
      _buildPoolsOverview(pools),
    ]);
  }

  // Storage Overview — polished with gradient capacity bar
  Widget _buildStorageOverview(StorageProvider s) {
    final summary = (s.summary is Map) ? s.summary as Map<String, dynamic> : {};
    final totalDisks =
        (summary['disks'] is List) ? (summary['disks'] as List).length : 0;
    final totalPools =
        (summary['pools'] is List) ? (summary['pools'] as List).length : 0;
    final totalDatasets = (summary['datasets'] is List)
        ? (summary['datasets'] as List).length
        : 0;
    final totalCapacity = summary['total_capacity'] ?? '--';

    final usedPct = (summary['used_pct'] is num)
        ? (summary['used_pct'] as num).toDouble()
        : 0.0;
    final usedClamped = (usedPct / 100).clamp(0.0, 1.0);

    return GlassCard(
      title: 'Storage Overview',
      icon: Icons.storage_rounded,
      titleColor: Colors.white,
      iconColor: Colors.tealAccent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            _statTile('Disks', '$totalDisks'),
            const SizedBox(width: 12),
            _statTile('Pools', '$totalPools'),
            const SizedBox(width: 12),
            _statTile('Datasets', '$totalDatasets'),
            const Spacer(),
            Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
              const Text('Total Capacity',
                  style: TextStyle(color: Colors.grey, fontSize: 12)),
              const SizedBox(height: 6),
              Text(totalCapacity.toString(),
                  style: const TextStyle(
                      fontWeight: FontWeight.bold, fontSize: 16)),
            ]),
          ]),
          const SizedBox(height: 16),
          // Gradient usage bar — TrueNAS style
          Container(
            height: 14,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              color: Colors.grey.shade900,
            ),
            child: LayoutBuilder(builder: (ctx, c) {
              final w = c.maxWidth * usedClamped;
              return Stack(children: [
                Positioned.fill(
                  child: Container(),
                ),
                AnimatedContainer(
                  duration: const Duration(milliseconds: 600),
                  width: w,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                        colors: [Color(0xFF00C6FF), Color(0xFF0072FF)]),
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ]);
            }),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Text('Used: ${(usedPct).round()}%',
                  style: const TextStyle(fontWeight: FontWeight.bold)),
              const Spacer(),
              Text('Available: ${summary['available'] ?? '--'}',
                  style: const TextStyle(color: Colors.grey)),
            ],
          ),
          const SizedBox(height: 12),
          Row(children: [
            ElevatedButton.icon(
              onPressed: () => s.loadSummary(),
              icon: const Icon(Icons.refresh),
              label: const Text('Refresh'),
              style: ElevatedButton.styleFrom(minimumSize: const Size(120, 40)),
            ),
            const SizedBox(width: 12),
            OutlinedButton.icon(
              onPressed: () => Navigator.pushNamed(context, '/storage'),
              icon: const Icon(Icons.open_in_new),
              label: const Text('Open Storage'),
            ),
          ]),
        ],
      ),
    );
  }

  Widget _statTile(String label, String value) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
      const SizedBox(height: 6),
      Text(value,
          style: const TextStyle(
              fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
    ]);
  }

  // Pools overview — with capacity gradient and health badges
  Widget _buildPoolsOverview(ZfsProvider zfs) {
    final pools = zfs.pools;
    if (pools.isEmpty) {
      return GlassCard(
        title: 'ZFS Pools',
        icon: Icons.pool,
        titleColor: Colors.white,
        child: const Padding(
            padding: EdgeInsets.all(12),
            child:
                Text('No pools found', style: TextStyle(color: Colors.grey))),
      );
    }

    return GlassCard(
      title: 'ZFS Pools',
      icon: Icons.pool,
      titleColor: Colors.white,
      child: Column(
        children: pools.map<Widget>((p) {
          final capacity = (p['capacity'] is num)
              ? (p['capacity'] as num).toDouble()
              : double.tryParse(p['capacity']?.toString() ?? '') ?? 0.0;
          final health = (p['health'] ?? 'UNKNOWN').toString();
          final name = (p['name'] ?? 'pool').toString();

          final color = health == 'ONLINE'
              ? Colors.greenAccent.shade400
              : (health == 'DEGRADED' ? Colors.orangeAccent : Colors.redAccent);

          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 8.0),
            child: InkWell(
              onTap: () =>
                  Navigator.pushNamed(context, '/pool', arguments: name),
              child: Row(
                children: [
                  CircleAvatar(
                      backgroundColor: color,
                      child: const Icon(Icons.layers, color: Colors.black)),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(name,
                              style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white)),
                          const SizedBox(height: 6),
                          _capacityBar(capacity),
                        ]),
                  ),
                  const SizedBox(width: 12),
                  Text('${capacity.round()}%',
                      style: const TextStyle(fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _capacityBar(double pct) {
    final v = (pct / 100).clamp(0.0, 1.0);
    return SizedBox(
      height: 12,
      child: LayoutBuilder(builder: (ctx, c) {
        final w = c.maxWidth;
        return Stack(children: [
          Container(
            width: w,
            height: 12,
            decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(6),
                color: Colors.grey.shade900),
          ),
          AnimatedContainer(
            duration: const Duration(milliseconds: 600),
            width: w * v,
            height: 12,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(6),
              gradient: LinearGradient(colors: [
                Color.lerp(Colors.greenAccent, Colors.blueAccent, v) ??
                    Colors.greenAccent,
                Color.lerp(Colors.tealAccent, Colors.indigoAccent, v) ??
                    Colors.indigoAccent
              ]),
            ),
          ),
        ]);
      }),
    );
  }

  // Datasets overview (compact list)
  Widget _buildDatasetsOverview(ZfsProvider zfs) {
    final datasets = zfs.datasets;
    return GlassCard(
      title: 'Datasets',
      icon: Icons.folder,
      titleColor: Colors.white,
      child: datasets.isEmpty
          ? const Padding(
              padding: EdgeInsets.all(12),
              child: Text('No datasets', style: TextStyle(color: Colors.grey)))
          : Column(
              children: datasets.take(8).map<Widget>((d) {
                final name = d['name'] ?? 'dataset';
                final used = d['used'] ?? '-';
                final avail = d['available'] ?? '-';
                return ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading:
                      const Icon(Icons.folder_open, color: Colors.tealAccent),
                  title:
                      Text(name, style: const TextStyle(color: Colors.white)),
                  subtitle: Text('Used: $used • Free: $avail',
                      style: const TextStyle(color: Colors.grey)),
                );
              }).toList(),
            ),
    );
  }

  // Disks grid — glass tiles, SMART temp, SSD/HDD iconography
  Widget _buildDisksGrid(StorageProvider s) {
    final summary = (s.summary is Map) ? s.summary as Map<String, dynamic> : {};
    final disks =
        (summary['disks'] is List) ? (summary['disks'] as List) : <dynamic>[];

    if (disks.isEmpty) {
      return GlassCard(
          title: 'Disks',
          icon: Icons.storage_rounded,
          titleColor: Colors.white,
          child: const Padding(
              padding: EdgeInsets.all(12),
              child: Text('No disks', style: TextStyle(color: Colors.grey))));
    }

    final width = MediaQuery.of(context).size.width;
    final crossAxisCount = width >= 1400 ? 3 : (width >= 1000 ? 2 : 1);

    return GlassCard(
      title: 'Disks',
      icon: Icons.storage_rounded,
      titleColor: Colors.white,
      child: GridView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: crossAxisCount,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 2.6,
        ),
        itemCount: disks.length,
        itemBuilder: (ctx, i) {
          final d = disks[i] as Map;
          final isHdd = d['rotational'] == true;
          final dev = d['devpath'] ?? '/dev/${d['name']}';
          final size = d['size_human'] ??
              (d['size_bytes'] != null ? _humanSize(d['size_bytes']) : '--');
          final model = d['model'] ?? 'Unknown';
          final smart =
              (d['smart'] is Map) ? d['smart'] as Map : <String, dynamic>{};
          final temp = smart['temperature'] is num
              ? (smart['temperature'] as num).toInt()
              : null;
          final health = smart['health'] ?? 'OK';

          final healthColor = health == 'OK'
              ? Colors.greenAccent
              : (health == 'WARN' ? Colors.orangeAccent : Colors.redAccent);

          return Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              color: const Color(0xFF0F1724),
              border: Border.all(color: Colors.white.withOpacity(0.03)),
            ),
            child: Row(children: [
              CircleAvatar(
                radius: 22,
                backgroundColor: isHdd
                    ? Colors.blueGrey.shade800
                    : Colors.deepPurple.shade700,
                child: Icon(isHdd ? Icons.sd_storage : Icons.memory,
                    color: Colors.white),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(dev,
                          style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              color: Colors.white)),
                      const SizedBox(height: 6),
                      Text('$model • $size',
                          style: const TextStyle(
                              color: Colors.grey, fontSize: 12)),
                    ]),
              ),
              Column(children: [
                if (temp != null)
                  Row(children: [
                    Icon(Icons.thermostat, size: 16, color: _tempColor(temp)),
                    const SizedBox(width: 6),
                    Text('$temp°C',
                        style: const TextStyle(color: Colors.white)),
                  ]),
                const SizedBox(height: 8),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                  decoration: BoxDecoration(
                      color: healthColor.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(8)),
                  child: Text(health.toString(),
                      style: TextStyle(
                          color: healthColor,
                          fontWeight: FontWeight.bold,
                          fontSize: 12)),
                ),
              ])
            ]),
          );
        },
      ),
    );
  }

  Color _tempColor(int t) {
    if (t < 40) return Colors.greenAccent;
    if (t < 50) return Colors.orangeAccent;
    return Colors.redAccent;
  }

  static String _humanSize(num bytes) {
    final units = ['B', 'K', 'M', 'G', 'T', 'P'];
    double b = bytes.toDouble();
    var i = 0;
    while (b >= 1024 && i < units.length - 1) {
      b /= 1024;
      i++;
    }
    if (i == 0) return '${b.toInt()}${units[i]}';
    return '${b.toStringAsFixed(1)}${units[i]}';
  }
}

/// MetricPanel used on left side
class MetricPanel extends StatelessWidget {
  final MonitoringProvider monitor;
  const MetricPanel({super.key, required this.monitor});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      title: 'System Metrics',
      icon: Icons.monitor,
      titleColor: Colors.white,
      child: Column(
        children: [
          Row(children: [
            Expanded(child: MetricCard(label: 'CPU', value: monitor.cpu)),
            const SizedBox(width: 8),
            Expanded(child: MetricCard(label: 'RAM', value: monitor.ram)),
          ]),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: MetricCard(label: 'Disk', value: monitor.disk)),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Network',
                        style: TextStyle(fontSize: 12, color: Colors.grey)),
                    const SizedBox(height: 6),
                    Text(
                        '${(monitor.netUp / 1024).toStringAsFixed(1)} KB/s ↑ • ${(monitor.netDown / 1024).toStringAsFixed(1)} KB/s ↓',
                        style: const TextStyle(color: Colors.white)),
                  ]),
            ),
          ])
        ],
      ),
    );
  }
}
