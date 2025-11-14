// lib/pages/datasets_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/zfs_provider.dart';

class DatasetsPage extends StatefulWidget {
  const DatasetsPage({super.key});

  @override
  State<DatasetsPage> createState() => _DatasetsPageState();
}

class _DatasetsPageState extends State<DatasetsPage> {
  String? _selectedPool;

  @override
  void initState() {
    super.initState();
    Future.microtask(() => context.read<ZfsProvider>().loadPools());
  }

  @override
  Widget build(BuildContext context) {
    final zfs = context.watch<ZfsProvider>();
    final pools = zfs.pools;

    return Scaffold(
      appBar: AppBar(title: const Text('Datasets')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            DropdownButtonFormField<String>(
              initialValue: _selectedPool,
              items: pools
                  .map<DropdownMenuItem<String>>((p) => DropdownMenuItem(
                      value: p['name'], child: Text(p['name'])))
                  .toList(),
              hint: const Text('Select pool'),
              onChanged: (v) async {
                setState(() => _selectedPool = v);
                if (v != null) {
                  await context.read<ZfsProvider>().loadDatasets(v);
                }
              },
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: _selectedPool == null
                  ? null
                  : () => _showCreateDatasetDialog(context, _selectedPool!),
              child: const Text('Create Dataset'),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView(
                children: (_selectedPool == null
                        ? []
                        : (zfs.datasets[_selectedPool] ?? []))
                    .map((d) => Card(
                            child: ListTile(
                          title: Text(d['name']),
                          subtitle: Text('mount: ${d['mountpoint']}'),
                        )))
                    .toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showCreateDatasetDialog(BuildContext ctx, String pool) {
    final nameCtrl = TextEditingController();
    final mountCtrl = TextEditingController();

    showDialog(
        context: ctx,
        builder: (context) {
          return AlertDialog(
            title: const Text('Create Dataset'),
            content: Column(mainAxisSize: MainAxisSize.min, children: [
              TextField(
                  controller: nameCtrl,
                  decoration: const InputDecoration(labelText: 'Name')),
              TextField(
                  controller: mountCtrl,
                  decoration: const InputDecoration(
                      labelText: 'Mountpoint (optional)')),
            ]),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel')),
              ElevatedButton(
                  onPressed: () async {
                    final name = nameCtrl.text.trim();
                    final mount = mountCtrl.text.trim().isEmpty
                        ? null
                        : mountCtrl.text.trim();
                    if (name.isEmpty) return;
                    try {
                      await context
                          .read<ZfsProvider>()
                          .createDataset(pool, name, mountpoint: mount);
                      ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Dataset created')));
                    } catch (e) {
                      ScaffoldMessenger.of(context)
                          .showSnackBar(SnackBar(content: Text('Error: $e')));
                    }
                    Navigator.pop(context);
                  },
                  child: const Text('Create'))
            ],
          );
        });
  }
}
