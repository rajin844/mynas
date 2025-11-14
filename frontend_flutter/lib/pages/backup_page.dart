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

    // SAFE: No use_build_context_synchronously warning.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      context.read<BackupProvider>().loadBackups();
    });
  }

  @override
  Widget build(BuildContext context) {
    final prov = context.watch<BackupProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('Backups')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            ElevatedButton(
              onPressed: () async {
                try {
                  await prov.createBackup();
                  if (!context.mounted) return;

                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Backup created')),
                  );
                } catch (e) {
                  if (!context.mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error: $e')),
                  );
                }
              },
              child: const Text('Create Backup'),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.builder(
                itemCount: prov.backups.length,
                itemBuilder: (ctx, i) {
                  final b = prov.backups[i];

                  return ListTile(
                    title: Text(b.toString()),
                    trailing: IconButton(
                      icon: const Icon(Icons.restore),
                      onPressed: () async {
                        final ctx = context; // Store context before async
                        try {
                          await prov.restore(b.toString());
                          if (!context.mounted) return;

                          ScaffoldMessenger.of(ctx).showSnackBar(
                            const SnackBar(content: Text('Restored')),
                          );
                        } catch (e) {
                          if (!context.mounted) return;
                          ScaffoldMessenger.of(ctx).showSnackBar(
                            SnackBar(content: Text('Error: $e')),
                          );
                        }
                      },
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
}
