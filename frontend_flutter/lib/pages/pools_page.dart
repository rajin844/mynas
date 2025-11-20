import 'package:flutter/material.dart';
import 'package:frontend_flutter/providers/storage_provider.dart';
import 'package:provider/provider.dart';
import '../providers/zfs_provider.dart';

class PoolsPage extends StatefulWidget {
  const PoolsPage({super.key});

  @override
  State<PoolsPage> createState() => _PoolsPageState();
}

class _PoolsPageState extends State<PoolsPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) return;
      await context.read<ZfsProvider>().loadPools();
    });
  }

  @override
  Widget build(BuildContext context) {
    final zfs = context.watch<ZfsProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text("ZFS Pools")),
      floatingActionButton: FloatingActionButton(
        //onPressed: () => _createPool(context),
        //child: const Icon(Icons.add),
        onPressed: () => _openPoolWizard(context),
        child: const Icon(Icons.add),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView.builder(
          itemCount: zfs.pools.length,
          itemBuilder: (context, i) {
            final p = zfs.pools[i];
            return Card(
              child: ListTile(
                leading: const Icon(Icons.storage),
                title: Text(p["name"]),
                subtitle: Text("Health: ${p["health"]} • Size: ${p["size"]}"),
                trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                  IconButton(
                      icon: const Icon(Icons.info_outline),
                      onPressed: () => _status(context, p["name"])),
                  IconButton(
                      icon: const Icon(Icons.cleaning_services),
                      onPressed: () =>
                          context.read<ZfsProvider>().scrubPool(p["name"])),
                  IconButton(
                      icon: const Icon(Icons.delete, color: Colors.red),
                      onPressed: () =>
                          context.read<ZfsProvider>().destroyPool(p["name"])),
                ]),
              ),
            );
          },
        ),
      ),
    );
  }

  void _status(BuildContext ctx, String pool) async {
    final provider = ctx.read<ZfsProvider>();
    final status = await provider.poolStatus(pool);

    showDialog(
        context: ctx,
        builder: (_) => AlertDialog(
              title: Text("Pool Status: $pool"),
              content: SingleChildScrollView(child: Text(status.toString())),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(ctx),
                    child: const Text("Close"))
              ],
            ));
  }

  void _createPool(BuildContext context) {
    final nameCtrl = TextEditingController();
    final devicesCtrl = TextEditingController();
    final raidzCtrl = TextEditingController(); // optional

    bool dryRun = true;

    showDialog(
      context: context,
      builder: (_) => StatefulBuilder(
        builder: (ctx, setState) {
          return AlertDialog(
            title: const Text("Create Pool"),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: nameCtrl,
                  decoration: const InputDecoration(labelText: "Pool Name"),
                ),
                TextField(
                  controller: devicesCtrl,
                  decoration: const InputDecoration(
                      labelText: "Devices (/dev/sdb,/dev/sdc)"),
                ),
                TextField(
                  controller: raidzCtrl,
                  decoration:
                      const InputDecoration(labelText: "RAID Level (optional)"),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Checkbox(
                        value: dryRun,
                        onChanged: (v) => setState(() => dryRun = v!)),
                    const Text("Dry Run (Preview Only)")
                  ],
                ),
              ],
            ),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text("Cancel")),
              ElevatedButton(
                child: const Text("Preview"),
                onPressed: () async {
                  final prov = context.read<ZfsProvider>();
                  final devices =
                      devicesCtrl.text.split(",").map((e) => e.trim()).toList();

                  final preview = await prov.previewPool(
                    nameCtrl.text.trim(),
                    devices,
                    raidz: raidzCtrl.text.trim().isEmpty
                        ? null
                        : raidzCtrl.text.trim(),
                  );

                  Navigator.pop(ctx);
                  _showDryRunPreview(context, preview, nameCtrl.text.trim(),
                      devices, raidzCtrl.text.trim());
                },
              )
            ],
          );
        },
      ),
    );
  }

  void _showDryRunPreview(
    BuildContext context,
    dynamic preview,
    String pool,
    List<String> devices,
    String? raidz,
  ) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text("Pool Create Preview"),
        content: SizedBox(
          width: 450,
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("Command:", style: TextStyle(fontWeight: FontWeight.bold)),
                Text(preview["cmd"] ?? "N/A"),
                const SizedBox(height: 12),
                Text("Warnings:",
                    style: TextStyle(fontWeight: FontWeight.bold)),
                Text(preview["warnings"]?.join("\n") ?? "None"),
                const SizedBox(height: 12),
                Text("Errors:", style: TextStyle(fontWeight: FontWeight.bold)),
                Text(preview["errors"]?.join("\n") ?? "None"),
                const SizedBox(height: 12),
                Text("Estimated Usable:",
                    style: TextStyle(fontWeight: FontWeight.bold)),
                Text("${preview["estimated_usable"] ?? 'N/A'} bytes"),
                const SizedBox(height: 12),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Cancel")),
          ElevatedButton(
            onPressed: preview["errors"] != null && preview["errors"].isNotEmpty
                ? null
                : () async {
                    final prov = context.read<ZfsProvider>();
                    await prov.createPool(
                      pool,
                      devices,
                      raidz: raidz!.isEmpty ? null : raidz,
                    );
                    Navigator.pop(context);
                  },
            child: const Text("Create (Real)"),
          ),
        ],
      ),
    );
  }

  void _openPoolWizard(BuildContext context) {
    final zfs = context.read<ZfsProvider>();
    final storage = context.read<StorageProvider>();

    final nameCtrl = TextEditingController();
    List<String> selectedDisks = [];
    String raidLevel = "stripe";

    showDialog(
      context: context,
      builder: (_) => StatefulBuilder(
        builder: (ctx, setState) {
          return AlertDialog(
            title: const Text("Create ZFS Pool"),
            content: SizedBox(
              width: 600,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // ---------------- POOL NAME ----------------
                  TextField(
                    controller: nameCtrl,
                    decoration: const InputDecoration(labelText: "Pool Name"),
                  ),

                  const SizedBox(height: 16),

                  // ---------------- DISK PICKER ----------------
                  Row(
                    children: [
                      const Text("Select Disks:",
                          style: TextStyle(
                              fontSize: 16, fontWeight: FontWeight.bold)),
                      const Spacer(),
                      TextButton(
                        onPressed: () async => await storage.loadDisks(),
                        child: const Text("Refresh"),
                      )
                    ],
                  ),

                  SizedBox(
                    height: 200,
                    child: ListView.builder(
                      itemCount: storage.disks.length,
                      itemBuilder: (context, i) {
                        final d = storage.disks[i];
                        final dev = "/dev/${d['name']}";

                        return CheckboxListTile(
                          value: selectedDisks.contains(dev),
                          title: Text("$dev (${d['size']})"),
                          subtitle: Text(
                              "${d['model'] ?? '-'} • ${d['vendor'] ?? '-'}"),
                          onChanged: (v) {
                            setState(() {
                              if (v == true) {
                                selectedDisks.add(dev);
                              } else {
                                selectedDisks.remove(dev);
                              }
                            });
                          },
                        );
                      },
                    ),
                  ),

                  const SizedBox(height: 20),

                  // ---------------- RAIDZ BUILDER ----------------
                  const Text("RAID Level:",
                      style:
                          TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),

                  DropdownButton<String>(
                    value: raidLevel,
                    items: const [
                      DropdownMenuItem(
                          value: "single", child: Text("Single Disk")),
                      DropdownMenuItem(
                          value: "stripe", child: Text("Stripe (RAID 0)")),
                      DropdownMenuItem(
                          value: "mirror", child: Text("Mirror RAID 1")),
                      DropdownMenuItem(value: "raidz1", child: Text("RAIDZ1")),
                      DropdownMenuItem(value: "raidz2", child: Text("RAIDZ2")),
                      DropdownMenuItem(value: "raidz3", child: Text("RAIDZ3")),
                    ],
                    onChanged: (v) => setState(() => raidLevel = v!),
                  ),

                  const SizedBox(height: 15),

                  // RAID RULES / WARNINGS
                  _raidWarnings(raidLevel, selectedDisks.length),
                ],
              ),
            ),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text("Cancel")),

              /// PREVIEW BUTTON
              ElevatedButton(
                onPressed: selectedDisks.isEmpty || nameCtrl.text.isEmpty
                    ? null
                    : () async {
                        final preview = await zfs.previewPool(
                          nameCtrl.text.trim(),
                          selectedDisks,
                          raidz: raidLevel == "stripe" ? null : raidLevel,
                        );

                        Navigator.pop(ctx);
                        _showPreviewDialog(context, preview,
                            nameCtrl.text.trim(), selectedDisks, raidLevel);
                      },
                child: const Text("Preview"),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _raidWarnings(String raid, int count) {
    String msg = "";
    Color color = Colors.orange;

    switch (raid) {
      case "mirror":
        if (count < 2) msg = "Mirror requires at least 2 disks";
        break;

      case "raidz1":
        if (count < 3) msg = "RAIDZ1 requires 3 or more disks";
        break;

      case "raidz2":
        if (count < 4) msg = "RAIDZ2 requires 4 or more disks";
        break;

      case "raidz3":
        if (count < 5) msg = "RAIDZ3 requires 5 or more disks";
        break;

      default:
        msg = "Stripe: No redundancy (1+ disks)";
        color = Colors.blue;
    }

    return Text(msg,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w600,
        ));
  }
}

void _showPreviewDialog(
  BuildContext context,
  dynamic preview,
  String pool,
  List<String> devices,
  String? raidz,
) {
  showDialog(
    context: context,
    builder: (_) => AlertDialog(
      title: const Text("Pool Create Preview (Dry Run)"),
      content: SizedBox(
        width: 500,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // COMMAND
              const Text("Command:",
                  style: TextStyle(fontWeight: FontWeight.bold)),
              Text(preview["cmd"] ?? "No command"),
              const SizedBox(height: 12),

              // WARNINGS
              const Text("Warnings:",
                  style: TextStyle(fontWeight: FontWeight.bold)),
              Text(
                (preview["warnings"] ?? []).isNotEmpty
                    ? preview["warnings"].join("\n")
                    : "None",
              ),
              const SizedBox(height: 12),

              // ERRORS
              const Text("Errors:",
                  style: TextStyle(fontWeight: FontWeight.bold)),
              Text(
                (preview["errors"] ?? []).isNotEmpty
                    ? preview["errors"].join("\n")
                    : "None",
                style: const TextStyle(color: Colors.red),
              ),
              const SizedBox(height: 12),

              // ESTIMATED SIZE
              const Text("Estimated usable space:",
                  style: TextStyle(fontWeight: FontWeight.bold)),
              Text("${preview["estimated_usable"] ?? 'N/A'} bytes"),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          child: const Text("Close"),
          onPressed: () => Navigator.pop(context),
        ),

        // DISABLE if errors exist
        ElevatedButton(
          onPressed: (preview["errors"] ?? []).isNotEmpty
              ? null
              : () async {
                  await context.read<ZfsProvider>().createPool(
                        pool,
                        devices,
                        raidz: raidz!.isEmpty ? null : raidz,
                      );
                  Navigator.pop(context);
                },
          child: const Text("Create Pool"),
        )
      ],
    ),
  );
}
