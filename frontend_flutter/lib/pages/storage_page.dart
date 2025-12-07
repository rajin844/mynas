import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/storage_provider.dart';
import '../services/websocket_service.dart';
import '../widgets/disk_card.dart';

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
    final ws = context.read<WebSocketService>();

    // Initial load
    Future.microtask(() async {
      await storage.loadSummary();
      await storage.loadDisks();
    });

    // Realtime updates
    ws.stream.listen((msg) {
      if (!mounted) return;
      if (msg is Map &&
          (msg["module"] == "storage" || msg["module"] == "disk")) {
        storage.loadSummary();
        storage.loadDisks();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final storage = context.watch<StorageProvider>();

    final diskCount = (storage.summary["disks"] is List)
        ? storage.summary["disks"].length
        : (storage.summary["disks"] ?? 0);
    final totalCap = storage.summary["capacity"] ?? "--";

    return Scaffold(
      appBar: AppBar(title: const Text("Storage Overview")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // ---------------- SUMMARY CARDS ----------------
            Row(
              children: [
                _summaryCard("Total Disks", diskCount.toString()),
                const SizedBox(width: 12),
                _summaryCard("Total Capacity", totalCap.toString()),
              ],
            ),

            const SizedBox(height: 24),

            // ---------------- ACTION BUTTONS ----------------
            Row(
              children: [
                ElevatedButton.icon(
                  onPressed: () async => await storage.loadDisks(),
                  icon: const Icon(Icons.refresh),
                  label: const Text("Detect Disks"),
                ),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                  onPressed: () async => await storage.loadSummary(),
                  icon: const Icon(Icons.storage),
                  label: const Text("Rescan Storage"),
                ),
              ],
            ),

            const SizedBox(height: 20),

            // ---------------- DISK LIST ----------------
            Expanded(
              child: Card(
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
                elevation: 2,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Detected Disks",
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Expanded(
                        child: storage.disks.isEmpty
                            ? const Center(
                                child: Text(
                                  "No disks detected",
                                  style: TextStyle(color: Colors.grey),
                                ),
                              )
                            : ListView.builder(
                                itemCount: storage.disks.length,
                                itemBuilder: (context, index) {
                                  final d = storage.disks[index]
                                      as Map<String, dynamic>;
                                  return DiskCard(disk: d);
                                },
                              ),
                      ),
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

  Widget _summaryCard(String title, String value) {
    return Expanded(
      child: Card(
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                value,
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              )
            ],
          ),
        ),
      ),
    );
  }
}
