// lib/pages/zfs_manager_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/zfs_provider.dart';

class ZfsManagerPage extends StatefulWidget {
  const ZfsManagerPage({super.key});
  @override
  State<ZfsManagerPage> createState() => _ZfsManagerPageState();
}

class _ZfsManagerPageState extends State<ZfsManagerPage> {
  @override
  void initState() {
    super.initState();
    context.read<ZfsProvider>().loadPools();
    context.read<ZfsProvider>().loadAllDatasets();
  }

  @override
  Widget build(BuildContext context) {
    final zfs = context.watch<ZfsProvider>();
    return Scaffold(
      appBar: AppBar(title: const Text("ZFS Manager")),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(children: [
          Expanded(
              child: ListView.builder(
            itemCount: zfs.pools.length,
            itemBuilder: (_, i) {
              final p = zfs.pools[i];
              return Card(
                child: ListTile(
                  title: Text(p['name']),
                  subtitle: Text(
                      "Health: ${p['health'] ?? 'Unknown'} • Size: ${p['size'] ?? '-'}"),
                  leading: Icon(Icons.circle, color: healthColor(p['health'])),
                  trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                    IconButton(
                        icon: const Icon(Icons.info),
                        onPressed: () => _showStatus(p['name'])),
                    IconButton(
                        icon: const Icon(Icons.refresh),
                        onPressed: () => zfs.scrubPool(p['name'])),
                    IconButton(
                        icon: const Icon(Icons.import_export),
                        onPressed: () => _importExportDialog(p['name'])),
                    IconButton(
                        icon: const Icon(Icons.delete, color: Colors.red),
                        onPressed: () => _destroyConfirm(p['name'])),
                    IconButton(
                      icon: const Icon(Icons.sync),
                      onPressed: () => _showScrubProgress(p['name']),
                    ),
                  ]),
                ),
              );
            },
          ))
        ]),
      ),
    );
  }

  void _showStatus(String pool) async {
    final res = await context.read<ZfsProvider>().poolStatus(pool);
    showDialog(
        context: context,
        builder: (_) => AlertDialog(
              title: Text("Pool Status: $pool"),
              content: SingleChildScrollView(child: Text(res.toString())),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text("Close"))
              ],
            ));
  }

  void _importExportDialog(String pool) {
    showDialog(
        context: context,
        builder: (_) => AlertDialog(
              title: const Text("Import / Export"),
              content: const Text("Import or export pool."),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text("Cancel")),
                ElevatedButton(
                    onPressed: () async {
                      //await context.read<ZfsProvider>().importpool(pool);
                      Navigator.pop(context);
                    },
                    child: const Text("Import")),
                ElevatedButton(
                    onPressed: () async {
                     // await context.read<ZfsProvider>().exportPool(pool);
                      Navigator.pop(context);
                    },
                    child: const Text("Export")),
              ],
            ));
  }

  void _destroyConfirm(String pool) {
    showDialog(
        context: context,
        builder: (_) => AlertDialog(
              title: const Text("Destroy Pool"),
              content: Text(
                  "Are you sure you want to destroy pool $pool? This is destructive."),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text("Cancel")),
                ElevatedButton(
                    onPressed: () async {
                      await context.read<ZfsProvider>().destroyPool(pool);
                      Navigator.pop(context);
                    },
                    child: const Text("Destroy")),
              ],
            ));
  }

  Color healthColor(String h) {
    switch (h.toUpperCase()) {
      case "ONLINE":
      case "HEALTHY":
        return Colors.green;
      case "DEGRADED":
      case "FAULTED":
      case "UNAVAIL":
      case "OFFLINE":
        return Colors.red;
      default:
        return Colors.orange;
    }
  }

  Future<void> _showScrubProgress(String pool) async {
   // final res = await context.read<ZfsProvider>().scrubStatus(pool);
   // String txt = res["scan"] ?? "unknown";

    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: Text("Scrub: $pool"),
       // content: Text(txt),
      ),
    );
  }
}
