// lib/pages/backup_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/backup_provider.dart';

class BackupPage extends StatefulWidget {
  const BackupPage({super.key});
  @override
  State<BackupPage> createState() => _BackupPageState();
}

class _BackupPageState extends State<BackupPage> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => context.read<BackupProvider>().loadBackups());
  }

  @override
  Widget build(BuildContext context) {
    final prov = context.watch<BackupProvider>();
    return Scaffold(
      appBar: AppBar(title: const Text('Backups')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(children: [
          ElevatedButton(
              onPressed: () async {
                await prov.createBackup();
              },
              child: const Text('Create Backup')),
          const SizedBox(height: 12),
          Expanded(
              child: ListView.builder(
                  itemCount: prov.backups.length,
                  itemBuilder: (ctx, i) {
                    final b = prov.backups[i];
                    return ListTile(
                        title: Text(b.toString()),
                        trailing:
                            Row(mainAxisSize: MainAxisSize.min, children: [
                          IconButton(
                              icon: const Icon(Icons.restore),
                              onPressed: () => prov.restore(b.toString())),
                        ]));
                  })),
        ]),
      ),
    );
  }
}
