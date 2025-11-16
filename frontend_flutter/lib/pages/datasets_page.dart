import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/zfs_provider.dart';

class DatasetsPage extends StatefulWidget {
  const DatasetsPage({super.key});

  @override
  State<DatasetsPage> createState() => _DatasetsPageState();
}

class _DatasetsPageState extends State<DatasetsPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      () async => await context.read<ZfsProvider>().loadAllDatasets();
    });
  }

  @override
  Widget build(BuildContext context) {
    final zfs = context.watch<ZfsProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text("ZFS Datasets")),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _createDataset(context),
        child: const Icon(Icons.add),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView.builder(
            itemCount: zfs.datasets.length,
            itemBuilder: (context, i) {
              final d = zfs.datasets[i];
              return Card(
                child: ListTile(
                  leading: const Icon(Icons.folder),
                  title: Text(d["name"]),
                  subtitle: Text("Mountpoint: ${d['mountpoint']}"),
                  trailing: IconButton(
                      icon: const Icon(Icons.delete, color: Colors.red),
                      onPressed: () => _deleteDataset(context, d)),
                ),
              );
            }),
      ),
    );
  }

  void _createDataset(BuildContext ctx) {
    final poolCtrl = TextEditingController();
    final nameCtrl = TextEditingController();
    final mountCtrl = TextEditingController();

    showDialog(
        context: ctx,
        builder: (_) => AlertDialog(
              title: const Text("Create Dataset"),
              content: Column(mainAxisSize: MainAxisSize.min, children: [
                TextField(
                    controller: poolCtrl,
                    decoration: const InputDecoration(labelText: "Pool Name")),
                TextField(
                    controller: nameCtrl,
                    decoration:
                        const InputDecoration(labelText: "Dataset Name")),
                TextField(
                    controller: mountCtrl,
                    decoration: const InputDecoration(
                        labelText: "Mountpoint (optional)")),
              ]),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(ctx),
                    child: const Text("Cancel")),
                ElevatedButton(
                    onPressed: () {
                      ctx.read<ZfsProvider>().createDataset(
                            poolCtrl.text.trim(),
                            nameCtrl.text.trim(),
                            mountpoint: mountCtrl.text.trim().isEmpty
                                ? null
                                : mountCtrl.text.trim(),
                          );
                      Navigator.pop(ctx);
                    },
                    child: const Text("Create"))
              ],
            ));
  }

  void _deleteDataset(BuildContext ctx, dynamic d) {
    final parts = d["name"].split("/");
    final pool = parts.first;
    final dsName = parts.sublist(1).join("/");

    showDialog(
        context: ctx,
        builder: (_) => AlertDialog(
              title: const Text("Delete Dataset"),
              content: Text("Delete '${d["name"]}' permanently?"),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(ctx),
                    child: const Text("Cancel")),
                ElevatedButton(
                    onPressed: () {
                      ctx.read<ZfsProvider>().destroyDataset(pool, dsName);
                      Navigator.pop(ctx);
                    },
                    child: const Text("Delete"))
              ],
            ));
  }
}
