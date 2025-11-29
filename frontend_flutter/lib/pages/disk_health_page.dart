// lib/pages/disk_health_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/storage_provider.dart';
import '../services/api_service.dart';

class DiskHealthPage extends StatefulWidget {
  const DiskHealthPage({super.key});
  @override
  State<DiskHealthPage> createState() => _DiskHealthPageState();
}

class _DiskHealthPageState extends State<DiskHealthPage> {
  bool loading = false;
  Map<String, dynamic> smartResults = {};

  @override
  void initState() {
    super.initState();
    context.read<StorageProvider>().loadDisks();
  }

  Future<void> runSmart(String dev) async {
    setState(() => loading = true);
    try {
      final api = context.read<StorageProvider>().api;
      final res = await api.callRpc("STORAGE", "smartCheck", {"dev": dev});
      setState(() => smartResults[dev] = res);
    } catch (e) {
      setState(() => smartResults[dev] = {"error": e.toString()});
    }
    setState(() => loading = false);
  }

  @override
  Widget build(BuildContext context) {
    final storage = context.watch<StorageProvider>();
    return Scaffold(
      appBar: AppBar(title: const Text("Disk Health (SMART)")),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(children: [
          Expanded(
              child: ListView.builder(
                  itemCount: storage.disks.length,
                  itemBuilder: (_, i) {
                    final d = storage.disks[i];
                    final dev = d['devpath'] ?? "/dev/${d['name']}";
                    return Card(
                        child: ListTile(
                      title: Text("$dev (${d['size']})"),
                      subtitle:
                          Text("${d['model'] ?? '-'} • ${d['vendor'] ?? '-'}"),
                      trailing: ElevatedButton(
                          onPressed: () => runSmart(dev),
                          child: const Text("SMART")),
                      onTap: () {
                        showDialog(
                            context: context,
                            builder: (_) => AlertDialog(
                                  title: Text(dev),
                                  content: SingleChildScrollView(
                                      child: Text(
                                          "${smartResults[dev] ?? 'No results'}")),
                                  actions: [
                                    TextButton(
                                        onPressed: () => Navigator.pop(context),
                                        child: const Text("Close"))
                                  ],
                                ));
                      },
                    ));
                  })),
        ]),
      ),
    );
  }

  Widget _usageBar(int used, int size) {
    double pct = size == 0 ? 0 : used / size;
    return LinearProgressIndicator(value: pct);
  }
}
