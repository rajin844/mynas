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
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) return;
      await context.read<SharesProvider>().loadShares();
    });
  }

  @override
  Widget build(BuildContext context) {
    final prov = context.watch<SharesProvider>();

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
                  itemCount: prov.shares.length,
                  itemBuilder: (ctx, i) {
                    final s = prov.shares[i];
                    return Card(
                        child: ListTile(
                      title:
                          Text(s['name'] ?? s['sharedfoldername'] ?? 'share'),
                      subtitle: Text(s['path'] ?? s['sharedfoldername'] ?? ''),
                      trailing: IconButton(
                          icon: const Icon(Icons.delete),
                          onPressed: () async {
                            final id = s['uuid'] ?? s['name'];
                            try {
                              await context
                                  .read<SharesProvider>()
                                  .deleteShare(id);
                              if (!context.mounted) return;
                              ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('Deleted')));
                            } catch (e) {
                              if (!mounted) return;
                              ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text('Error: $e')));
                            }
                          }),
                    ));
                  }))
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
        builder: (_) {
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
                  onChanged: (v) {
                    protocol = v ?? 'smb';
                  }),
            ]),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Cancel')),
              ElevatedButton(
                  onPressed: () async {
                    final name = nameCtrl.text.trim();
                    final path = pathCtrl.text.trim();
                    if (name.isEmpty || path.isEmpty) return;
                    try {
                      await context
                          .read<SharesProvider>()
                          .createShare(name, path, protocol);
                      if (!context.mounted) return;
                      Navigator.pop(ctx);
                      ScaffoldMessenger.of(ctx).showSnackBar(
                          const SnackBar(content: Text('Share created')));
                    } catch (e) {
                      if (!mounted) return;
                      ScaffoldMessenger.of(ctx)
                          .showSnackBar(SnackBar(content: Text('Error: $e')));
                    }
                  },
                  child: const Text('Create')),
            ],
          );
        });
  }
}
