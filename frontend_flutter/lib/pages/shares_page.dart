// lib/pages/shares_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/shares_provider.dart';

class SharesPage extends StatefulWidget {
  const SharesPage({super.key});

  @override
  State<SharesPage> createState() => _SharesPageState();
}

class _SharesPageState extends State<SharesPage> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => context.read<SharesProvider>().loadShares());
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<SharesProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('Shares')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(children: [
          ElevatedButton.icon(
              icon: const Icon(Icons.add),
              label: const Text('Create Share'),
              onPressed: () => _showCreate(context)),
          const SizedBox(height: 12),
          Expanded(
            child: ListView.builder(
              itemCount: provider.shares.length,
              itemBuilder: (context, i) {
                final s = provider.shares[i];
                return Card(
                  child: ListTile(
                    title: Text(s['name'] ?? s['sharedfoldername'] ?? 'share'),
                    subtitle: Text(s['path'] ?? s['sharedfoldername'] ?? ''),
                    trailing: IconButton(
                      icon: const Icon(Icons.delete),
                      onPressed: () async {
                        final id = s['uuid'] ?? s['name'];
                        await provider.deleteShare(id);
                        ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Deleted')));
                      },
                    ),
                  ),
                );
              },
            ),
          )
        ]),
      ),
    );
  }

  void _showCreate(BuildContext ctx) {
    final nameCtrl = TextEditingController();
    final pathCtrl = TextEditingController();
    String protocol = 'smb';

    showDialog(
        context: ctx,
        builder: (context) {
          return AlertDialog(
            title: const Text('Create Share'),
            content: Column(mainAxisSize: MainAxisSize.min, children: [
              TextField(
                  controller: nameCtrl,
                  decoration: const InputDecoration(labelText: 'Name')),
              TextField(
                  controller: pathCtrl,
                  decoration: const InputDecoration(labelText: 'Path')),
              DropdownButtonFormField<String>(
                  initialValue: protocol,
                  items: const [
                    DropdownMenuItem(value: 'smb', child: Text('SMB')),
                    DropdownMenuItem(value: 'nfs', child: Text('NFS')),
                  ],
                  onChanged: (v) => protocol = v ?? 'smb'),
            ]),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel')),
              ElevatedButton(
                  onPressed: () async {
                    final name = nameCtrl.text.trim();
                    final path = pathCtrl.text.trim();
                    if (name.isEmpty || path.isEmpty) return;
                    await context
                        .read<SharesProvider>()
                        .createShare(name, path, protocol);
                    Navigator.pop(context);
                  },
                  child: const Text('Create')),
            ],
          );
        });
  }
}
