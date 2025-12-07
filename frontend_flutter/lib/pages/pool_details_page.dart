// lib/pages/pool_details_page.dart
import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/zfs_provider.dart';
import '../providers/smart_provider.dart';

/// PoolDetailsPage
/// route arguments: { "name": "<poolName>" }
class PoolDetailsPage extends StatefulWidget {
  const PoolDetailsPage({super.key});

  @override
  State<PoolDetailsPage> createState() => _PoolDetailsPageState();
}

class _PoolDetailsPageState extends State<PoolDetailsPage> {
  String? poolName;
  bool loading = true;
  Map<String, dynamic> pool = {};
  List<Map<String, dynamic>> vdevs = [];
  List<Map<String, dynamic>> datasets = [];
  List<Map<String, dynamic>> scrubHistory = [];
  double scrubProgress = 0.0;
  Timer? _pollTimer;

  @override
  void initState() {
    super.initState();
    // Wait until route args are available
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map && args.containsKey('name')) {
        poolName = args['name'] as String;
        _init();
      } else {
        // If none provided, pop
        Navigator.pop(context);
      }
    });

    // Optionally listen to websocket updates via providers (if implemented)
    // For example you could subscribe to a WebSocketService here.
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _init() async {
    setState(() => loading = true);
    await _refresh();
    // Poll scrub progress periodically (optional)
    _pollTimer =
        Timer.periodic(const Duration(seconds: 5), (_) => _pollProgress());
    setState(() => loading = false);
  }

  Future<void> _refresh() async {
    if (poolName == null) return;
    final zfs = context.read<ZfsProvider>();
    final smart = context.read<SmartProvider>();

    try {
      final p = await zfs.getPoolDetails(poolName!);
      final ds = await zfs.listDatasetsForPool(poolName!);
      final history = await zfs.getScrubHistory(poolName!);
      final progress = await zfs.getScrubProgress(poolName!);

      await smart.loadSmartForPool(poolName!);

      setState(() {
        pool = p ?? {};
        vdevs = List<Map<String, dynamic>>.from(
            p?['vdevs'] ?? p?['vdev_list'] ?? p?['devices'] ?? []);
        datasets = List<Map<String, dynamic>>.from(ds ?? []);
        scrubHistory = List<Map<String, dynamic>>.from(history ?? []);
        scrubProgress = (progress ?? 0.0).clamp(0.0, 100.0) / 100.0;
      });
    } catch (e) {
      // Defensive: don't crash UI
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load pool details: $e')));
    }
  }

  Future<void> _pollProgress() async {
    if (poolName == null) return;
    final zfs = context.read<ZfsProvider>();
    try {
      final p = await zfs.getScrubProgress(poolName!);
      if (!mounted) return;
      setState(() => scrubProgress = (p ?? 0.0).clamp(0.0, 100.0) / 100.0);
    } catch (_) {}
  }

  // Scrub controls
  Future<void> _startScrub() async {
    if (poolName == null) return;
    final zfs = context.read<ZfsProvider>();
    try {
      await zfs.startScrub(poolName!);
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Scrub started')));
      await _refresh();
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to start scrub: $e')));
    }
  }

  Future<void> _stopScrub() async {
    if (poolName == null) return;
    final zfs = context.read<ZfsProvider>();
    try {
      await zfs.stopScrub(poolName!);
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Scrub stopped')));
      await _refresh();
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to stop scrub: $e')));
    }
  }

  Future<void> _createDataset() async {
    final nameCtrl = TextEditingController();
    final mountCtrl = TextEditingController();
    final ok = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
              title: const Text('Create Dataset'),
              content: Column(mainAxisSize: MainAxisSize.min, children: [
                TextField(
                    controller: nameCtrl,
                    decoration:
                        const InputDecoration(labelText: 'Dataset name')),
                TextField(
                    controller: mountCtrl,
                    decoration: const InputDecoration(
                        labelText: 'Mountpoint (optional)')),
              ]),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(context, false),
                    child: const Text('Cancel')),
                ElevatedButton(
                    onPressed: () => Navigator.pop(context, true),
                    child: const Text('Create')),
              ],
            ));
    if (ok != true) return;
    try {
      await context.read<ZfsProvider>().createDataset(
          poolName!, nameCtrl.text.trim(),
          mountpoint:
              mountCtrl.text.trim().isEmpty ? null : mountCtrl.text.trim());
      await _refresh();
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Create dataset failed: $e')));
    }
  }

  Color _poolHealthColor() {
    final s = (pool['health'] ?? pool['status'] ?? 'UNKNOWN')
        .toString()
        .toUpperCase();
    if (s.contains('ONLINE') || s.contains('OK') || s.contains('HEALTHY'))
      return Colors.green;
    if (s.contains('DEGRADED') || s.contains('WARN')) return Colors.orange;
    return Colors.red;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Pool: ${poolName ?? ""}'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _refresh),
          PopupMenuButton<String>(
            onSelected: (v) async {
              if (v == 'start_scrub') await _startScrub();
              if (v == 'stop_scrub') await _stopScrub();
              if (v == 'create_ds') await _createDataset();
            },
            itemBuilder: (ctx) => [
              const PopupMenuItem(
                  value: 'start_scrub', child: Text('Start scrub')),
              const PopupMenuItem(
                  value: 'stop_scrub', child: Text('Stop scrub')),
              const PopupMenuDivider(),
              const PopupMenuItem(
                  value: 'create_ds', child: Text('Create dataset')),
            ],
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(12),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // top summary row
                    Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(child: _buildPoolSummaryCard()),
                          const SizedBox(width: 12),
                          SizedBox(width: 360, child: _buildSmartPanel()),
                        ]),
                    const SizedBox(height: 16),

                    // VDEV visualizer card
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('VDEV Layout',
                                  style:
                                      TextStyle(fontWeight: FontWeight.w600)),
                              const SizedBox(height: 8),
                              VdevVisualizer(vdevs: vdevs),
                              const SizedBox(height: 8),
                              Text('VDEVs: ${vdevs.length}',
                                  style: const TextStyle(
                                      fontSize: 12, color: Colors.grey)),
                            ]),
                      ),
                    ),

                    const SizedBox(height: 16),

                    // scrub controls & history
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Scrub & Repair',
                                  style:
                                      TextStyle(fontWeight: FontWeight.w600)),
                              const SizedBox(height: 8),
                              Row(children: [
                                ElevatedButton.icon(
                                    onPressed: _startScrub,
                                    icon: const Icon(Icons.play_arrow),
                                    label: const Text('Start Scrub')),
                                const SizedBox(width: 8),
                                OutlinedButton.icon(
                                    onPressed: _stopScrub,
                                    icon: const Icon(Icons.stop),
                                    label: const Text('Stop Scrub')),
                                const Spacer(),
                                Text(
                                    'Progress: ${(scrubProgress * 100).toStringAsFixed(1)}%'),
                              ]),
                              const SizedBox(height: 8),
                              LinearProgressIndicator(
                                  value: scrubProgress, minHeight: 10),
                              const SizedBox(height: 12),
                              const Text('Scrub History',
                                  style:
                                      TextStyle(fontWeight: FontWeight.w600)),
                              const SizedBox(height: 8),
                              SizedBox(
                                height: 140,
                                child: scrubHistory.isEmpty
                                    ? const Center(
                                        child: Text('No scrub history'))
                                    : ListView.builder(
                                        itemCount: scrubHistory.length,
                                        itemBuilder: (ctx, i) {
                                          final r = scrubHistory[i];
                                          final ts = r['ts'] ??
                                              r['when'] ??
                                              r['date'] ??
                                              r['created_at'] ??
                                              '';
                                          final result = r['status'] ??
                                              r['result'] ??
                                              r['outcome'] ??
                                              'OK';
                                          return ListTile(
                                            dense: true,
                                            title: Text('$ts'),
                                            subtitle: Text(
                                                r['note']?.toString() ?? ''),
                                            trailing: Text(result.toString()),
                                          );
                                        }),
                              ),
                            ]),
                      ),
                    ),

                    const SizedBox(height: 16),

                    // datasets grid
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(children: [
                                const Expanded(
                                    child: Text('Datasets',
                                        style: TextStyle(
                                            fontWeight: FontWeight.w600))),
                                ElevatedButton.icon(
                                    onPressed: _createDataset,
                                    icon: const Icon(Icons.add),
                                    label: const Text('Create')),
                              ]),
                              const SizedBox(height: 8),
                              datasets.isEmpty
                                  ? const Padding(
                                      padding: EdgeInsets.all(12),
                                      child: Text('No datasets'))
                                  : GridView.builder(
                                      shrinkWrap: true,
                                      physics:
                                          const NeverScrollableScrollPhysics(),
                                      gridDelegate:
                                          const SliverGridDelegateWithFixedCrossAxisCount(
                                              crossAxisCount: 2,
                                              mainAxisSpacing: 8,
                                              crossAxisSpacing: 8,
                                              childAspectRatio: 3.8),
                                      itemCount: datasets.length,
                                      itemBuilder: (ctx, i) {
                                        final d = datasets[i];
                                        return DatasetCard(
                                            dataset: d,
                                            poolName: poolName ?? '');
                                      }),
                            ]),
                      ),
                    ),
                    const SizedBox(height: 24),
                  ]),
            ),
    );
  }

  Widget _buildPoolSummaryCard() {
    // read multiple possible keys
    final cap = pool['size'] ?? pool['capacity'] ?? pool['total'] ?? 0;
    final used = pool['alloc'] ?? pool['allocated'] ?? pool['used'] ?? 0;
    final health = pool['health'] ?? pool['status'] ?? 'UNKNOWN';

    double pct = 0;
    try {
      final pcap = double.tryParse(cap.toString()) ?? 0;
      final pused = double.tryParse(used.toString()) ?? 0;
      pct = pcap <= 0 ? 0 : ((pused / pcap) * 100.0);
      if (pct.isNaN) pct = 0;
    } catch (_) {
      pct = 0;
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(
                child: Text(poolName ?? '',
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.bold))),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
              decoration: BoxDecoration(
                  color: _poolHealthColor().withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8)),
              child: Row(children: [
                Icon(Icons.circle, size: 10, color: _poolHealthColor()),
                const SizedBox(width: 8),
                Text(health.toString())
              ]),
            ),
          ]),
          const SizedBox(height: 12),
          Text('${pct.toStringAsFixed(1)}% used',
              style: const TextStyle(fontSize: 13)),
          const SizedBox(height: 6),
          LinearProgressIndicator(
              value: (pct / 100.0).clamp(0.0, 1.0), minHeight: 10),
          const SizedBox(height: 12),
          Row(children: [
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Capacity',
                  style: TextStyle(fontSize: 12, color: Colors.grey)),
              Text(cap.toString(),
                  style: const TextStyle(fontWeight: FontWeight.bold)),
            ]),
            const SizedBox(width: 20),
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Allocated',
                  style: TextStyle(fontSize: 12, color: Colors.grey)),
              Text(used.toString(),
                  style: const TextStyle(fontWeight: FontWeight.bold)),
            ]),
            const Spacer(),
            ElevatedButton.icon(
                onPressed: _refresh,
                icon: const Icon(Icons.sync),
                label: const Text('Refresh')),
          ])
        ]),
      ),
    );
  }

  Widget _buildSmartPanel() {
    final smartProv = context.watch<SmartProvider>();
    final smartList = smartProv.poolSmart[poolName] ?? [];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('SMART & Disk Health',
              style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          smartList.isEmpty
              ? const Padding(
                  padding: EdgeInsets.all(8), child: Text('No SMART data'))
              : Column(
                  children: smartList.map<Widget>((d) {
                    final temp = d['temperature'] ?? d['temp'] ?? 0;
                    final health = d['health'] ?? d['state'] ?? 'UNKNOWN';
                    final model = d['model'] ?? d['model_name'] ?? '';
                    final name = d['device'] ?? d['name'] ?? '?';
                    final history = List<double>.from((d['history'] ?? []).map(
                        (e) => (e is num)
                            ? e.toDouble()
                            : double.tryParse(e.toString()) ?? 0.0));
                    final spark = history.isEmpty
                        ? List<double>.generate(
                            8, (i) => 20 + Random().nextInt(30).toDouble())
                        : history;
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 6),
                      child: Row(children: [
                        Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(name,
                                  style: const TextStyle(
                                      fontWeight: FontWeight.bold)),
                              const SizedBox(height: 4),
                              Text(model,
                                  style: const TextStyle(
                                      fontSize: 12, color: Colors.grey)),
                            ]),
                        const SizedBox(width: 8),
                        Expanded(child: _Sparkline(values: spark, height: 36)),
                        const SizedBox(width: 8),
                        Column(children: [
                          Text('${temp}°C',
                              style:
                                  const TextStyle(fontWeight: FontWeight.bold)),
                          const SizedBox(height: 4),
                          Text(health.toString(),
                              style: const TextStyle(fontSize: 12)),
                        ])
                      ]),
                    );
                  }).toList(),
                ),
        ]),
      ),
    );
  }
}

/// VdevVisualizer (mirror/raidz/single)
class VdevVisualizer extends StatelessWidget {
  final List<Map<String, dynamic>> vdevs;
  const VdevVisualizer({super.key, required this.vdevs});

  @override
  Widget build(BuildContext context) {
    if (vdevs.isEmpty) {
      return const Center(child: Text('No VDEVs detected'));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: vdevs.map((v) {
        final type =
            (v['type'] ?? v['layout'] ?? (v['name'] ?? 'single')).toString();
        final disks = List<Map<String, dynamic>>.from(
            v['disks'] ?? v['devices'] ?? v['members'] ?? []);
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(type.toUpperCase(),
                style: const TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            _renderVdev(type, disks),
          ]),
        );
      }).toList(),
    );
  }

  Widget _renderVdev(String type, List<Map<String, dynamic>> disks) {
    if (type.contains('mirror')) {
      return Row(children: disks.map((d) => DiskSmallCard(disk: d)).toList());
    } else if (type.startsWith('raidz')) {
      return Column(children: [
        Row(children: disks.map((d) => DiskSmallCard(disk: d)).toList()),
        const SizedBox(height: 6),
        Text('vdev (${type.toUpperCase()}) — ${disks.length} disks',
            style: const TextStyle(fontSize: 12, color: Colors.grey)),
      ]);
    } else {
      return Row(children: disks.map((d) => DiskSmallCard(disk: d)).toList());
    }
  }
}

class DiskSmallCard extends StatelessWidget {
  final Map<String, dynamic> disk;
  const DiskSmallCard({super.key, required this.disk});

  @override
  Widget build(BuildContext context) {
    final name = disk['name'] ?? disk['devpath'] ?? disk['device'] ?? 'sd?';
    final model = disk['model'] ?? disk['model_name'] ?? '';
    final size = disk['size'] ?? disk['size_text'] ?? '';
    final rotational = disk['rotational'] == true || disk['rotational'] == 1;
    final color = rotational ? Colors.blue.shade50 : Colors.green.shade50;
    final icon = rotational ? Icons.storage : Icons.memory;

    return Container(
      width: 120,
      margin: const EdgeInsets.only(right: 8),
      padding: const EdgeInsets.all(8),
      decoration:
          BoxDecoration(borderRadius: BorderRadius.circular(8), color: color),
      child: Column(children: [
        Icon(icon, size: 28),
        const SizedBox(height: 6),
        Text(name,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text(size.toString(), style: const TextStyle(fontSize: 11)),
        const SizedBox(height: 4),
        Text(model, style: const TextStyle(fontSize: 10, color: Colors.grey)),
      ]),
    );
  }
}

/// Dataset card used in the grid
class DatasetCard extends StatelessWidget {
  final Map dataset;
  final String poolName;
  const DatasetCard({super.key, required this.dataset, required this.poolName});

  @override
  Widget build(BuildContext context) {
    final name = dataset['name'] ?? dataset['dataset'] ?? '';
    final mount = dataset['mountpoint'] ?? dataset['mount'] ?? '';
    final compress = dataset['compression'] ?? dataset['compress'] ?? 'off';
    final quota = dataset['quota'] ?? dataset['quota_bytes'] ?? '';

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.grey.shade200)),
      child: Row(children: [
        const Icon(Icons.folder),
        const SizedBox(width: 8),
        Expanded(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(name, style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text('Mount: ${mount.isEmpty ? '-' : mount}',
              style: const TextStyle(fontSize: 12)),
          const SizedBox(height: 4),
          Text('Compression: $compress • Quota: $quota',
              style: const TextStyle(fontSize: 11, color: Colors.grey)),
        ])),
        PopupMenuButton<String>(
          onSelected: (v) {
            if (v == 'props') {
              // TODO: open dataset properties editor
            } else if (v == 'snapshot') {
              // TODO: open snapshot dialog
            }
          },
          itemBuilder: (_) => [
            const PopupMenuItem(value: 'props', child: Text('Properties')),
            const PopupMenuItem(value: 'snapshot', child: Text('Snapshot')),
          ],
        )
      ]),
    );
  }
}

/// Simple sparkline widget (no external libs)
class _Sparkline extends StatelessWidget {
  final List<double> values;
  final double height;
  const _Sparkline({super.key, required this.values, this.height = 28});

  @override
  Widget build(BuildContext context) {
    final max = values.isEmpty ? 1.0 : values.reduce((a, b) => a > b ? a : b);
    final min = values.isEmpty ? 0.0 : values.reduce((a, b) => a < b ? a : b);
    final range = (max - min).abs() < 0.0001 ? 1.0 : (max - min);
    return SizedBox(
      height: height,
      child: Row(
        children: values.map((v) {
          final norm = (v - min) / range;
          return Expanded(
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 2),
              height: height * (0.2 + 0.8 * norm),
              decoration: BoxDecoration(
                  color: Colors.blueAccent,
                  borderRadius: BorderRadius.circular(3)),
            ),
          );
        }).toList(),
      ),
    );
  }
}
