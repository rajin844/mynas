// lib/pages/pools_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/zfs_provider.dart';

class PoolsPage extends StatefulWidget {
  const PoolsPage({super.key});

  @override
  State<PoolsPage> createState() => _PoolsPageState();
}

class _PoolsPageState extends State<PoolsPage> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => context.read<ZfsProvider>().loadPools());
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<ZfsProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('Pools')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            ElevatedButton.icon(
              icon: const Icon(Icons.add),
              label: const Text('Create Pool (Dry-Run)'),
              onPressed: () => _showCreatePoolDialog(context),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.builder(
                itemCount: provider.pools.length,
                itemBuilder: (context, i) {
                  final p = provider.pools[i];
                  return Card(
                    child: ListTile(
                      title: Text(p['name'] ?? p['pool'] ?? 'unknown'),
                      subtitle: Text('health: ${p['health'] ?? ''}'),
                      trailing: IconButton(
                        icon: const Icon(Icons.refresh),
                        onPressed: () =>
                            context.read<ZfsProvider>().loadPools(),
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showCreatePoolDialog(BuildContext ctx) {
    final nameCtrl = TextEditingController();
    final devicesCtrl = TextEditingController();

    showDialog(
      context: ctx,
      builder: (context) {
        return AlertDialog(
          title: const Text('Create Pool (dry-run)'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                  controller: nameCtrl,
                  decoration: const InputDecoration(labelText: 'Pool name')),
              TextField(
                  controller: devicesCtrl,
                  decoration: const InputDecoration(
                      labelText: 'Devices (comma separated)')),
            ],
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context),
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
                // call storage RPC via provider (use ApiService directly via provider if needed)
                try {
                  await context
                      .read<ZfsProvider>()
                      .api
                      .createPool(name, devices, dryRun: true);
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                      content: Text(
                          'Dry-run OK — confirm in CLI or UI to execute')));
                } catch (e) {
                  ScaffoldMessenger.of(context)
                      .showSnackBar(SnackBar(content: Text('Error: $e')));
                }
                Navigator.pop(context);
              },
              child: const Text('Dry Run'),
            ),
          ],
        );
      },
    );
  }
}
