import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/zfs_provider.dart';
import '../providers/smart_provider.dart';

class PoolCard extends StatefulWidget {
  final Map<String, dynamic> pool;
  const PoolCard({super.key, required this.pool});

  @override
  State<PoolCard> createState() => _PoolCardState();
}

class _PoolCardState extends State<PoolCard> {
  bool expanded = false;
  bool loadingTopology = false;
  Map<String, dynamic>? topology;

  Color _healthColor(String status) {
    final s = status.toUpperCase();
    if (s.contains('ONLINE') || s.contains('OK') || s.contains('HEALTHY'))
      return Colors.green;
    if (s.contains('DEGRADED') || s.contains('WARN')) return Colors.orange;
    return Colors.red;
  }

  @override
  Widget build(BuildContext context) {
    final zfs = context.read<ZfsProvider>();
    final pool = widget.pool;
    final name =
        pool['name'] ?? pool['pool_name'] ?? pool['id']?.toString() ?? 'pool';
    final health = pool['health'] ?? pool['status'] ?? 'UNKNOWN';
    final used = pool['alloc'] ??
        pool['used'] ??
        pool['allocated'] ??
        pool['usage'] ??
        0;
    final size = pool['size'] ?? pool['capacity'] ?? pool['total'] ?? 0;

    double pct = 0;
    try {
      final usedNum = double.tryParse(used.toString()) ?? 0;
      final sizeNum = double.tryParse(size.toString()) ?? 0;
      if (sizeNum > 0) pct = (usedNum / sizeNum).clamp(0.0, 1.0);
    } catch (_) {
      pct = 0;
    }

    return Card(
      elevation: 2,
      child: InkWell(
        onTap: () =>
            Navigator.pushNamed(context, '/pool', arguments: {'name': name}),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(name,
                          style: const TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 16)),
                      const SizedBox(height: 6),
                      Text('Health: $health',
                          style: TextStyle(color: _healthColor(health))),
                    ]),
              ),
              IconButton(
                icon: Icon(expanded ? Icons.expand_less : Icons.expand_more),
                onPressed: () async {
                  setState(() => expanded = !expanded);
                  if (expanded) {
                    setState(() => loadingTopology = true);
                    await zfs.loadTopology(name);
                    setState(() {
                      topology = zfs.vdevTopology;
                      loadingTopology = false;
                    });
                  }
                },
              )
            ]),
            const SizedBox(height: 8),
            LinearProgressIndicator(value: pct, minHeight: 8),
            const SizedBox(height: 6),
            Row(children: [
              Text('${(pct * 100).toStringAsFixed(1)}% used'),
              const Spacer(),
              IconButton(
                  tooltip: 'Start scrub',
                  onPressed: () async {
                    await zfs.startScrub(name);
                    ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Scrub started')));
                  },
                  icon: const Icon(Icons.play_arrow)),
              IconButton(
                  tooltip: 'Stop scrub',
                  onPressed: () async {
                    await zfs.stopScrub(name);
                    ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Scrub stopped')));
                  },
                  icon: const Icon(Icons.stop)),
              PopupMenuButton<String>(
                onSelected: (v) async {
                  if (v == 'destroy') {
                    final ok = await showDialog<bool>(
                        context: context,
                        builder: (_) => AlertDialog(
                              title: const Text('Destroy Pool'),
                              content: Text(
                                  'Destroy pool $name? This will remove data.'),
                              actions: [
                                TextButton(
                                    onPressed: () =>
                                        Navigator.pop(context, false),
                                    child: const Text('Cancel')),
                                ElevatedButton(
                                    onPressed: () =>
                                        Navigator.pop(context, true),
                                    child: const Text('Destroy')),
                              ],
                            ));
                    if (ok == true) {
                      await zfs.destroyPool(name);
                      ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Pool destroyed')));
                    }
                  } else if (v == 'details') {
                    Navigator.pushNamed(context, '/pool',
                        arguments: {'name': name});
                  }
                },
                itemBuilder: (_) => [
                  const PopupMenuItem(
                      value: 'details', child: Text('Open details')),
                  const PopupMenuItem(
                      value: 'destroy',
                      child:
                          Text('Destroy', style: TextStyle(color: Colors.red))),
                ],
              ),
            ]),
            if (expanded) const SizedBox(height: 8),
            if (expanded)
              loadingTopology
                  ? const Center(
                      child: Padding(
                          padding: EdgeInsets.all(12),
                          child: CircularProgressIndicator()))
                  : topology == null
                      ? const Text('No topology')
                      : VdevTextView(
                          raw: topology?['raw'] ??
                              topology?['text'] ??
                              topology?.toString() ??
                              ''),
          ]),
        ),
      ),
    );
  }
}

class VdevTextView extends StatelessWidget {
  final String raw;
  const VdevTextView({super.key, required this.raw});

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 80),
      padding: const EdgeInsets.all(8),
      color: Colors.grey.shade50,
      child: SingleChildScrollView(
          child: Text(raw,
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12))),
    );
  }
}
