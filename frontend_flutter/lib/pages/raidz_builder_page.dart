// lib/pages/raidz_builder_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/storage_provider.dart';
import '../providers/zfs_provider.dart';

class RaidzBuilderPage extends StatefulWidget {
  const RaidzBuilderPage({super.key});
  @override
  State<RaidzBuilderPage> createState() => _RaidzBuilderPageState();
}

class _RaidzBuilderPageState extends State<RaidzBuilderPage> {
  final nameCtrl = TextEditingController();
  String raid = "raidz1";
  List<String> selected = [];

  @override
  void initState() {
    super.initState();
    context.read<StorageProvider>().loadDisks();
  }

  @override
  Widget build(BuildContext context) {
    final storage = context.watch<StorageProvider>();
    final zfs = context.read<ZfsProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text("RAIDZ Builder")),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            TextField(
                controller: nameCtrl,
                decoration: const InputDecoration(labelText: "Pool Name")),
            const SizedBox(height: 8),
            Row(children: [
              const Text("RAID Type:"),
              const SizedBox(width: 8),
              DropdownButton<String>(
                value: raid,
                items: const [
                  DropdownMenuItem(value: "stripe", child: Text("Stripe")),
                  DropdownMenuItem(value: "mirror", child: Text("Mirror")),
                  DropdownMenuItem(value: "raidz1", child: Text("RAIDZ1")),
                  DropdownMenuItem(value: "raidz2", child: Text("RAIDZ2")),
                  DropdownMenuItem(value: "raidz3", child: Text("RAIDZ3")),
                ],
                onChanged: (v) => setState(() => raid = v!),
              )
            ]),
            const SizedBox(height: 12),

            // Disk picker
            Expanded(
                child: _diskPicker(storage, selected, (dev, add) {
              setState(() => selected = List.from(selected)
                ..removeWhere((e) => e == dev)
                ..addAll(add ? [dev] : []));
            })),

            const SizedBox(height: 12),
            Row(children: [
              ElevatedButton(
                onPressed: selected.isEmpty || nameCtrl.text.trim().isEmpty
                    ? null
                    : () async {
                        final preview = await zfs.previewPool(
                            nameCtrl.text.trim(), selected,
                            raidz: raid == "stripe" ? null : raid);
                        _showPreview(
                            preview, nameCtrl.text.trim(), selected, raid);
                      },
                child: const Text("Preview (Dry Run)"),
              ),
              const SizedBox(width: 12),
              ElevatedButton(
                onPressed: selected.isEmpty || nameCtrl.text.trim().isEmpty
                    ? null
                    : () async {
                        final confirmed = await showDialog<bool>(
                            context: context,
                            builder: (_) => AlertDialog(
                                  title: const Text("Confirm Create"),
                                  content: const Text(
                                      "This will create a pool on selected disks. Continue?"),
                                  actions: [
                                    TextButton(
                                        onPressed: () =>
                                            Navigator.pop(context, false),
                                        child: const Text("Cancel")),
                                    ElevatedButton(
                                        onPressed: () =>
                                            Navigator.pop(context, true),
                                        child: const Text("Create")),
                                  ],
                                ));
                        if (confirmed == true) {
                          await zfs.createPool(nameCtrl.text.trim(), selected,
                              raidz: raid == "stripe" ? null : raid);
                          ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                  content: Text("Pool create requested")));
                        }
                      },
                child: const Text("Create (No Preview)"),
              )
            ])
          ],
        ),
      ),
    );
  }

  Widget _diskPicker(StorageProvider storage, List<String> selected,
      Function(String, bool) onToggle) {
    return Card(
      child: ListView.builder(
        itemCount: storage.disks.length,
        itemBuilder: (_, i) {
          final d = storage.disks[i];
          final dev = d['devpath'] ?? "/dev/${d['name']}";
          final size = d['size'] ?? '';
          final subtitle = "${d['model'] ?? '-'} • ${d['vendor'] ?? '-'}";
          final disabled = (d['mountpoint'] != null && d['mountpoint'] != '') ||
              dev == "/dev/sda"; // simple system disk disable
          return CheckboxListTile(
            value: selected.contains(dev),
            onChanged: disabled ? null : (v) => onToggle(dev, v!),
            title: Text("$dev ($size)"),
            subtitle: Text(subtitle + (disabled ? " • system/used" : "")),
          );
        },
      ),
    );
  }

  void _showPreview(
      dynamic preview, String pool, List<String> devices, String raid) {
    showDialog(
        context: context,
        builder: (_) => AlertDialog(
              title: const Text("Preview"),
              content: SingleChildScrollView(
                  child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Command: ${preview['cmd'] ?? 'N/A'}"),
                  const SizedBox(height: 8),
                  Text(
                      "Estimated usable: ${preview['estimated_usable'] ?? 'N/A'} bytes"),
                  const SizedBox(height: 8),
                  Text("VDEVs: ${preview['vdevs']?.toString() ?? 'N/A'}"),
                  const SizedBox(height: 8),
                  Text("Warnings: ${(preview['warnings'] ?? []).join(', ')}"),
                  const SizedBox(height: 8),
                  Text("Errors: ${(preview['errors'] ?? []).join(', ')}",
                      style: const TextStyle(color: Colors.red)),
                ],
              )),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text("Close")),
                ElevatedButton(
                    onPressed: (preview['errors'] ?? []).isNotEmpty
                        ? null
                        : () async {
                            Navigator.pop(context);
                            await context.read<ZfsProvider>().createPool(
                                pool, devices,
                                raidz: raid == "stripe" ? null : raid);
                            ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                    content: Text("Pool create requested")));
                          },
                    child: const Text("Create Pool")),
              ],
            ));
  }
}
