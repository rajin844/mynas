import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/storage_provider.dart';

class StoragePage extends StatefulWidget {
  const StoragePage({super.key});

  @override
  State<StoragePage> createState() => _StoragePageState();
}

class _StoragePageState extends State<StoragePage> {
  @override
  void initState() {
    super.initState();
    final storage = context.read<StorageProvider>();

    Future.microtask(() async {
      await storage.loadSummary();
      await storage.loadDisks();
    });
  }

  @override
  Widget build(BuildContext context) {
    final storage = context.watch<StorageProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text("Storage Overview")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // ---------------- SUMMARY CARDS ----------------
            Row(
              children: [
                _summaryCard("Disks", storage.summary?["disks"] ?? 0),
                const SizedBox(width: 12),
                _summaryCard("Pools", storage.summary?["pools"] ?? 0),
                const SizedBox(width: 12),
                _summaryCard("Datasets", storage.summary?["datasets"] ?? 0),
              ],
            ),

            const SizedBox(height: 24),

            // ---------------- ACTION BUTTONS ----------------
            Row(
              children: [
                ElevatedButton.icon(
                    onPressed: () => storage.detectDisks(),
                    icon: const Icon(Icons.refresh),
                    label: const Text("Detect Disks")),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                    onPressed: () => storage.rescanSata(),
                    icon: const Icon(Icons.search),
                    label: const Text("Rescan SATA")),
              ],
            ),

            const SizedBox(height: 20),

            // ---------------- DISK LIST ----------------
            Expanded(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("Detected Disks",
                          style: TextStyle(
                              fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      Expanded(
                        child: ListView.builder(
                          itemCount: storage.disks.length,
                          itemBuilder: (context, i) {
                            final d = storage.disks[i];
                            return ListTile(
                              leading: const Icon(Icons.storage),
                              title: Text("/dev/${d['name']} (${d['size']})"),
                              subtitle: Text(
                                  "Model: ${d['model'] ?? '-'} | Vendor: ${d['vendor'] ?? '-'}"),
                            );
                          },
                        ),
                      )
                    ],
                  ),
                ),
              ),
            )
          ],
        ),
      ),
    );
  }

  Widget _summaryCard(String label, int value) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            children: [
              Text(label,
                  style: const TextStyle(
                      fontSize: 15, fontWeight: FontWeight.w500)),
              const SizedBox(height: 8),
              Text(
                value.toString(),
                style:
                    const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              )
            ],
          ),
        ),
      ),
    );
  }
}
