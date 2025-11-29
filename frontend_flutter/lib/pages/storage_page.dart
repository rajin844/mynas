import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/storage_provider.dart';
import '../services/websocket_service.dart';

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
      if (msg is Map && msg["module"] == "storage") {
        storage.loadSummary();
        storage.loadDisks();
      }
    });
  }

  // ====================================================================
  // SMART BOTTOM SHEET UI
  // ====================================================================

  void showSmartDialog(BuildContext context, Map<String, dynamic> smart) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) {
        final attrs = smart["attributes"] as List? ?? [];

        return Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Text(
                  "SMART Report",
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text("Model: ${smart["model"]}"),
              Text("Serial: ${smart["serial"]}"),
              Text("Health: ${smart["health"]}"),
              Text("Temperature: ${smart["temp"]}"),
              Text("Power-on Hours: ${smart["power_on_hours"]}"),
              const SizedBox(height: 12),
              const Text(
                "Attributes",
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 8),
              SizedBox(
                height: 300,
                child: ListView.builder(
                  itemCount: attrs.length,
                  itemBuilder: (context, i) {
                    final a = attrs[i];
                    return ListTile(
                      dense: true,
                      title: Text(a["name"]),
                      subtitle: Text("ID: ${a["id"]}"),
                      trailing: Text("${a["raw"]}"),
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  // ====================================================================
  // MAIN UI
  // ====================================================================

  @override
  Widget build(BuildContext context) {
    final storage = context.watch<StorageProvider>();

    final diskCount = storage.summary["disks"]?.length ?? 0;
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
                _summaryCard("Total Capacity", totalCap),
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
                                  final d = storage.disks[index];
                                  final dev =
                                      d["devpath"] ?? "/dev/${d['name']}";
                                  final model = d["model"] ?? "Unknown";
                                  final size = d["size_human"] ?? "--";

                                  final bool isHdd = d["rotational"] == true;

                                  return ListTile(
                                    leading: Icon(
                                      isHdd ? Icons.storage : Icons.bolt,
                                      color:
                                          isHdd ? Colors.blue : Colors.orange,
                                      size: 30,
                                    ),
                                    title: Text("$dev ($size)"),
                                    subtitle: Text("Model: $model"),

                                    // ================= SMART BUTTON =================
                                    trailing: ElevatedButton.icon(
                                      icon: const Icon(Icons.info),
                                      label: const Text("SMART"),
                                      onPressed: () async {
                                        // show loading
                                        showDialog(
                                          context: context,
                                          barrierDismissible: false,
                                          builder: (_) => const Center(
                                            child: CircularProgressIndicator(),
                                          ),
                                        );

                                        final smart =
                                            await storage.smartInfo(dev);

                                        if (!mounted) return;
                                        Navigator.pop(
                                            context); // remove loading

                                        if (smart == null) {
                                          ScaffoldMessenger.of(context)
                                              .showSnackBar(
                                            const SnackBar(
                                              content: Text(
                                                  "Unable to fetch SMART info"),
                                            ),
                                          );
                                          return;
                                        }

                                        showSmartDialog(context, smart);
                                      },
                                    ),
                                  );
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
