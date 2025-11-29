// lib/pages/snapshots_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

class SnapshotsPage extends StatefulWidget {
  const SnapshotsPage({super.key});
  @override
  State<SnapshotsPage> createState() => _SnapshotsPageState();
}

class _SnapshotsPageState extends State<SnapshotsPage> {
  List<dynamic> snaps = [];
  final nameCtrl = TextEditingController();
  final dsCtrl = TextEditingController();

  Future<void> load() async {
    final api = context.read<ApiService>();
    final res = await api.callRpc("SNAP", "list", {});
    setState(() => snaps = res ?? []);
  }

  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<ApiService>();
    return Scaffold(
      appBar: AppBar(title: const Text("Snapshots")),
      body: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(children: [
            Row(children: [
              Expanded(
                  child: TextField(
                      controller: dsCtrl,
                      decoration: const InputDecoration(labelText: "Dataset"))),
              const SizedBox(width: 8),
              Expanded(
                  child: TextField(
                      controller: nameCtrl,
                      decoration:
                          const InputDecoration(labelText: "Snapshot name"))),
              const SizedBox(width: 8),
              ElevatedButton(
                  onPressed: () async {
                    final r = await api.callRpc("SNAP", "create", {
                      "dataset": dsCtrl.text.trim(),
                      "name": nameCtrl.text.trim()
                    });
                    await load();
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                        content:
                            Text("Created: ${r['success'] ?? r.toString()}")));
                  },
                  child: const Text("Create"))
            ]),
            const SizedBox(height: 12),
            Expanded(
                child: ListView.builder(
                    itemCount: snaps.length,
                    itemBuilder: (_, i) {
                      final s = snaps[i];
                      return ListTile(
                        title: Text("${s['dataset']}@${s['name']}"),
                        trailing:
                            Row(mainAxisSize: MainAxisSize.min, children: [
                          IconButton(
                              icon: const Icon(Icons.restore),
                              onPressed: () async {
                                await api.callRpc("SNAP", "rollback", {
                                  "dataset": s['dataset'],
                                  "name": s['name']
                                });
                                await load();
                              }),
                        ]),
                      );
                    }))
          ])),
    );
  }
}
