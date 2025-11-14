import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/zfs_provider.dart';
import '../services/api_service.dart';

class PoolsPage extends StatefulWidget {
  const PoolsPage({super.key});
  @override
  State<PoolsPage> createState() => _PoolsPageState();
}

class _PoolsPageState extends State<PoolsPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      context.read<ZfsProvider>().loadPools();
    });
  }

  @override
  Widget build(BuildContext context) {
    final prov = context.watch<ZfsProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('Pools')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(children: [
          ElevatedButton.icon(
            icon: const Icon(Icons.add),
            label: const Text('Create Pool (Dry-Run)'),
            onPressed: () => _showCreatePoolDialog(context),
          ),
          const SizedBox(height: 12),
          Expanded(
              child: ListView.builder(
                  itemCount: prov.pools.length,
                  itemBuilder: (ctx, i) {
                    final p = prov.pools[i];
                    return Card(
                        child: ListTile(
                            title: Text(p['name'] ?? 'unknown'),
                            subtitle: Text('health: ${p['health'] ?? ''}'),
                            trailing: IconButton(
                                icon: const Icon(Icons.refresh),
                                onPressed: () => prov.loadPools())));
                  }))
        ]),
      ),
    );
  }

  void _showCreatePoolDialog(BuildContext ctx) {
    final nameCtrl = TextEditingController();
    final devicesCtrl = TextEditingController();

    showDialog(
        context: ctx,
        builder: (_) {
          return AlertDialog(
            title: const Text('Create Pool (dry-run)'),
            content: Column(mainAxisSize: MainAxisSize.min, children: [
              TextField(
                  controller: nameCtrl,
                  decoration: const InputDecoration(labelText: 'Pool name')),
              TextField(
                  controller: devicesCtrl,
                  decoration: const InputDecoration(
                      labelText: 'Devices (comma separated)')),
            ]),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Cancel')),
              ElevatedButton(
                  onPressed: () async {
                    final name = nameCtrl.text.trim();
                    final devices = devicesCtrl.text
                        .split(',')
                        .map((s) => s.trim())
                        .where((s) => s.isNotEmpty)
                        .toList();
                    if (name.isEmpty || devices.isEmpty) return;
                    try {
                      // use ApiService directly here for create_pool
                      final api = context.read<ApiService>();
                      await api.createPool(name, devices, dryRun: true);
                      if (!context.mounted) return;
                      Navigator.pop(ctx);
                      ScaffoldMessenger.of(ctx).showSnackBar(
                          const SnackBar(content: Text('Dry-run OK')));
                    } catch (e) {
                      if (!mounted) return;
                      ScaffoldMessenger.of(ctx)
                          .showSnackBar(SnackBar(content: Text('Error: $e')));
                    }
                  },
                  child: const Text('Dry Run'))
            ],
          );
        });
  }
}
