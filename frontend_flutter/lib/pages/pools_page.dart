// /root/mynas/frontend_flutter/lib/pages/pools_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/zfs_provider.dart';
import '../providers/storage_provider.dart';

class PoolsPage extends StatefulWidget {
  const PoolsPage({super.key});

  @override
  State<PoolsPage> createState() => _PoolsPageState();
}

class _PoolsPageState extends State<PoolsPage> {
  @override
  void initState() {
    super.initState();
    // load pools after first frame
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      context.read<ZfsProvider>().loadPools();
    });
  }

  @override
  Widget build(BuildContext context) {
    final zfs = context.watch<ZfsProvider>();
    final storage = context.watch<StorageProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text("ZFS Pools")),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _openPoolWizard(context),
        child: const Icon(Icons.add),
        tooltip: "Create Pool",
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: zfs.loadingPools
            ? const Center(child: CircularProgressIndicator())
            : zfs.pools.isEmpty
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text("No pools available",
                            style: TextStyle(fontSize: 16)),
                        const SizedBox(height: 8),
                        ElevatedButton(
                          onPressed: () =>
                              context.read<ZfsProvider>().loadPools(),
                          child: const Text("Refresh"),
                        ),
                      ],
                    ),
                  )
                : ListView.separated(
                    itemCount: zfs.pools.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (context, i) {
                      final p = zfs.pools[i] as Map<String, dynamic>;
                      final name = p["name"] ?? "unknown";
                      final health = (p["health"] ?? "UNKNOWN").toString();
                      final capacity =
                          _toDouble(p["capacity"]); // percent 0-100
                      final vdev =
                          p["vdev"] ?? p["vdev_layout"] ?? p["vdevs"] ?? "—";

                      return Card(
                        elevation: 2,
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8)),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 8),
                          child: Column(
                            children: [
                              Row(
                                children: [
                                  _healthBadge(health),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(name,
                                            style: const TextStyle(
                                                fontSize: 16,
                                                fontWeight: FontWeight.w600)),
                                        const SizedBox(height: 4),
                                        Text("VDEV: ${_vdevSummary(vdev)}",
                                            style:
                                                const TextStyle(fontSize: 12)),
                                      ],
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  IconButton(
                                    tooltip: "Status",
                                    icon: const Icon(Icons.info_outline),
                                    onPressed: () => _showStatus(context, name),
                                  ),
                                  IconButton(
                                    tooltip: "Scrub",
                                    icon: const Icon(Icons.cleaning_services),
                                    onPressed: () async {
                                      final ok = await context
                                          .read<ZfsProvider>()
                                          .scrubPool(name);
                                      if (!mounted) return;
                                      ScaffoldMessenger.of(context)
                                          .showSnackBar(
                                        SnackBar(
                                            content: Text(ok
                                                ? "Scrub started for $name"
                                                : "Failed to start scrub")),
                                      );
                                    },
                                  ),
                                  IconButton(
                                    tooltip: "Destroy",
                                    icon: const Icon(Icons.delete,
                                        color: Colors.red),
                                    onPressed: () =>
                                        _confirmDestroy(context, name),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              // capacity bar
                              Row(
                                children: [
                                  Expanded(
                                    child: LinearProgressIndicator(
                                      value: (capacity / 100).clamp(0.0, 1.0),
                                      minHeight: 8,
                                      backgroundColor: Colors.grey.shade200,
                                      valueColor: AlwaysStoppedAnimation(
                                          _capacityColor(capacity)),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Text("${capacity.toStringAsFixed(0)}%",
                                      style: const TextStyle(fontSize: 12)),
                                ],
                              ),
                              const SizedBox(height: 8),
                              // optional details row
                              Row(
                                children: [
                                  Text("Size: ${p["size"] ?? "-"}",
                                      style: const TextStyle(fontSize: 12)),
                                  const SizedBox(width: 12),
                                  Text("Allocated: ${p["allocated"] ?? "-"}",
                                      style: const TextStyle(fontSize: 12)),
                                  const Spacer(),
                                  Text("Type: ${p["type"] ?? "zfs"}",
                                      style: const TextStyle(fontSize: 12)),
                                ],
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
      ),
    );
  }

  // -------------------------
  // Helpers
  // -------------------------
  double _toDouble(dynamic v) {
    if (v == null) return 0.0;
    if (v is double) return v;
    if (v is int) return v.toDouble();
    if (v is String) return double.tryParse(v) ?? 0.0;
    return 0.0;
  }

  Color _capacityColor(double pct) {
    if (pct < 60) return Colors.green;
    if (pct < 85) return Colors.orange;
    return Colors.red;
  }

  Widget _healthBadge(String health) {
    final h = health.toLowerCase();
    Color bg;
    IconData icon;
    String label = health.toUpperCase();

    if (h.contains("online") || h.contains("healthy") || h.contains("ok")) {
      bg = Colors.green.shade100;
      icon = Icons.check_circle;
    } else if (h.contains("degraded") || h.contains("warning")) {
      bg = Colors.orange.shade100;
      icon = Icons.warning;
    } else {
      bg = Colors.red.shade100;
      icon = Icons.error;
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.all(6),
          decoration:
              BoxDecoration(color: bg, borderRadius: BorderRadius.circular(6)),
          child: Row(children: [
            Icon(icon, size: 16, color: Colors.black87),
            const SizedBox(width: 6),
            Text(label,
                style:
                    const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
          ]),
        ),
      ],
    );
  }

  String _vdevSummary(dynamic vdev) {
    if (vdev == null) return "—";
    if (vdev is String) return vdev;
    try {
      return vdev.toString();
    } catch (_) {
      return "—";
    }
  }

  // -------------------------
  // Actions & Dialogs
  // -------------------------
  void _showStatus(BuildContext ctx, String pool) async {
    final prov = ctx.read<ZfsProvider>();
    final status = await prov.poolStatus(pool);
    if (!mounted) return;
    showDialog(
      context: ctx,
      builder: (_) => AlertDialog(
        title: Text("Pool Status: $pool"),
        content: SingleChildScrollView(child: Text(status.toString())),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text("Close")),
        ],
      ),
    );
  }

  void _confirmDestroy(BuildContext ctx, String pool) {
    showDialog(
      context: ctx,
      builder: (dialogCtx) => AlertDialog(
        title: Text("Destroy Pool"),
        content:
            Text("Permanently destroy pool \"$pool\"? This cannot be undone."),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(dialogCtx),
              child: const Text("Cancel")),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () async {
              Navigator.pop(dialogCtx); // close confirm
              final ok = await context.read<ZfsProvider>().destroyPool(pool);
              if (!mounted) return;
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                  content: Text(ok ? "Pool destroyed" : "Destroy failed")));
              await context.read<ZfsProvider>().loadPools();
            },
            child: const Text("Destroy"),
          ),
        ],
      ),
    );
  }

  // Full wizard / builder (TrueNAS-style simplified)
  void _openPoolWizard(BuildContext context) {
    final nameCtrl = TextEditingController();
    final devices = <String>[];
    String raidLevel = "stripe";
    bool dryRun = true;

    // initial disks from StorageProvider
    final storage = context.read<StorageProvider>();
    // ensure we have the latest disks
    storage.loadSummary();

    showDialog(
      context: context,
      builder: (dialogCtx) {
        return StatefulBuilder(builder: (ctx, setState) {
          final availableDisks = storage.disks;
          return AlertDialog(
            title: const Text("Create ZFS Pool"),
            content: SizedBox(
              width: 700,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Pool name
                  TextField(
                      controller: nameCtrl,
                      decoration:
                          const InputDecoration(labelText: "Pool name")),
                  const SizedBox(height: 12),

                  // Disk picker
                  Row(
                    children: [
                      const Text("Select disks",
                          style: TextStyle(fontWeight: FontWeight.w600)),
                      const Spacer(),
                      TextButton(
                          onPressed: () => storage.loadSummary(),
                          child: const Text("Refresh")),
                    ],
                  ),
                  SizedBox(
                    height: 200,
                    child: availableDisks.isEmpty
                        ? const Center(child: Text("No disks detected"))
                        : ListView.builder(
                            itemCount: availableDisks.length,
                            itemBuilder: (_, idx) {
                              final d =
                                  availableDisks[idx] as Map<String, dynamic>;
                              final dev = d["devpath"] ?? "/dev/${d['name']}";
                              final label =
                                  "${dev} • ${d['size'] ?? ''} • ${d['model'] ?? ''}";
                              final selected = devices.contains(dev);

                              return CheckboxListTile(
                                title: Text(label),
                                value: selected,
                                onChanged: (v) {
                                  setState(() {
                                    if (v == true) {
                                      devices.add(dev);
                                    } else {
                                      devices.remove(dev);
                                    }
                                  });
                                },
                              );
                            },
                          ),
                  ),
                  const SizedBox(height: 12),

                  // RAID level
                  Row(children: const [
                    Text("RAID level:",
                        style: TextStyle(fontWeight: FontWeight.w600))
                  ]),
                  const SizedBox(height: 6),
                  DropdownButton<String>(
                    value: raidLevel,
                    items: const [
                      DropdownMenuItem(
                          value: "single", child: Text("Single Disk")),
                      DropdownMenuItem(
                          value: "stripe", child: Text("Stripe (RAID 0)")),
                      DropdownMenuItem(
                          value: "mirror", child: Text("Mirror (RAID 1)")),
                      DropdownMenuItem(value: "raidz1", child: Text("RAIDZ1")),
                      DropdownMenuItem(value: "raidz2", child: Text("RAIDZ2")),
                      DropdownMenuItem(value: "raidz3", child: Text("RAIDZ3")),
                    ],
                    onChanged: (v) => setState(() => raidLevel = v ?? "stripe"),
                  ),
                  const SizedBox(height: 8),

                  // dry-run toggle
                  Row(children: [
                    Checkbox(
                        value: dryRun,
                        onChanged: (v) => setState(() => dryRun = v ?? true)),
                    const Text("Dry-run (preview)"),
                  ]),

                  const SizedBox(height: 6),
                  // quick rule hint
                  _raidRuleText(raidLevel, devices.length),
                ],
              ),
            ),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(dialogCtx),
                  child: const Text("Cancel")),
              ElevatedButton(
                onPressed: nameCtrl.text.trim().isEmpty || devices.isEmpty
                    ? null
                    : () async {
                        // do preview first (dry-run)
                        final zfs = context.read<ZfsProvider>();
                        final preview = await zfs.previewPool(
                            nameCtrl.text.trim(), devices,
                            raidz: raidLevel == "stripe" ? null : raidLevel);

                        if (!mounted) return;
                        Navigator.pop(dialogCtx); // close wizard

                        // show preview dialog
                        await _showPreviewAndMaybeCreate(
                            context,
                            nameCtrl.text.trim(),
                            devices,
                            raidLevel,
                            preview,
                            dryRun);
                      },
                child: const Text("Preview"),
              ),
            ],
          );
        });
      },
    );
  }

  Future<void> _showPreviewAndMaybeCreate(
      BuildContext context,
      String pool,
      List<String> devices,
      String raidLevel,
      dynamic preview,
      bool dryRun) async {
    // show preview
    if (!mounted) return;
    await showDialog(
      context: context,
      builder: (ctx) {
        final warnings = (preview?["warnings"] ?? []) as List? ?? [];
        final errors = (preview?["errors"] ?? []) as List? ?? [];
        final cmd = preview?["cmd"] ?? preview?["command"] ?? "N/A";
        final usable =
            preview?["estimated_usable"] ?? preview?["estimated"] ?? "N/A";

        return AlertDialog(
          title: const Text("Preview"),
          content: SizedBox(
            width: 600,
            child: SingleChildScrollView(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text("Command:",
                        style: TextStyle(fontWeight: FontWeight.bold)),
                    Text(cmd),
                    const SizedBox(height: 12),
                    const Text("Warnings:",
                        style: TextStyle(fontWeight: FontWeight.bold)),
                    Text(warnings.isEmpty ? "None" : warnings.join("\n")),
                    const SizedBox(height: 12),
                    const Text("Errors:",
                        style: TextStyle(fontWeight: FontWeight.bold)),
                    Text(errors.isEmpty ? "None" : errors.join("\n"),
                        style: TextStyle(
                            color: errors.isEmpty ? Colors.black : Colors.red)),
                    const SizedBox(height: 12),
                    const Text("Estimated usable:",
                        style: TextStyle(fontWeight: FontWeight.bold)),
                    Text("$usable"),
                  ]),
            ),
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text("Close")),
            ElevatedButton(
              onPressed: errors.isNotEmpty
                  ? null
                  : () async {
                      Navigator.pop(ctx);
                      // create if not dry-run
                      final prov = context.read<ZfsProvider>();
                      final res = await prov.createPool(pool, devices,
                          raidz: raidLevel == "stripe" ? null : raidLevel,
                          dryRun: dryRun);
                      if (!mounted) return;
                      final msg = dryRun
                          ? "Preview completed (dry-run)"
                          : "Create pool request submitted";
                      ScaffoldMessenger.of(context)
                          .showSnackBar(SnackBar(content: Text(msg)));
                      await prov.loadPools();
                    },
              child: Text(dryRun ? "Close (Dry Run)" : "Create Pool"),
            ),
          ],
        );
      },
    );
  }

  Widget _raidRuleText(String raid, int count) {
    String msg;
    Color color = Colors.blue;

    switch (raid) {
      case "mirror":
        msg = count < 2 ? "Mirror needs at least 2 disks" : "Mirror OK";
        color = count < 2 ? Colors.orange : Colors.green;
        break;
      case "raidz1":
        msg = count < 3 ? "RAIDZ1 needs 3+ disks" : "RAIDZ1 OK";
        color = count < 3 ? Colors.orange : Colors.green;
        break;
      case "raidz2":
        msg = count < 4 ? "RAIDZ2 needs 4+ disks" : "RAIDZ2 OK";
        color = count < 4 ? Colors.orange : Colors.green;
        break;
      case "raidz3":
        msg = count < 5 ? "RAIDZ3 needs 5+ disks" : "RAIDZ3 OK";
        color = count < 5 ? Colors.orange : Colors.green;
        break;
      case "single":
        msg = count < 1 ? "Select a disk" : "Single disk";
        color = count < 1 ? Colors.orange : Colors.blue;
        break;
      default:
        msg = "Stripe (no redundancy)";
    }

    return Padding(
      padding: const EdgeInsets.only(top: 6),
      child: Text(msg,
          style: TextStyle(color: color, fontWeight: FontWeight.w600)),
    );
  }

  @override
  void dispose() {
    super.dispose();
  }
}
