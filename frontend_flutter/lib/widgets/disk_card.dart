import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/storage_provider.dart';

class DiskCard extends StatelessWidget {
  final Map<String, dynamic> disk;
  final void Function(Map<String, dynamic> smart)? onSmart;

  const DiskCard({super.key, required this.disk, this.onSmart});

  String _devpath() {
    return disk['devpath'] ??
        disk['device'] ??
        (disk['name'] != null ? "/dev/${disk['name']}" : disk.toString());
  }

  String _label() {
    final name = disk['name'] ?? disk['model'] ?? _devpath();
    final size = disk['size_human'] ?? disk['size'] ?? '--';
    return "$name • $size";
  }

  @override
  Widget build(BuildContext context) {
    final storage = context.read<StorageProvider>();
    final dev = _devpath();
    final label = _label();
    final model = disk['model'] ?? disk['vendor'] ?? 'Unknown';
    final bool isHdd = disk['rotational'] == true;

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
          // Icon
          Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(isHdd ? Icons.storage : Icons.memory,
                size: 36, color: isHdd ? Colors.brown : Colors.blue),
          ]),
          const SizedBox(width: 12),

          // Info
          Expanded(
              child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Text("Device: $dev", style: const TextStyle(fontSize: 12)),
              Text("Model: $model", style: const TextStyle(fontSize: 12)),
            ],
          )),

          // Actions (SMART + menu)
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ElevatedButton.icon(
                icon: const Icon(Icons.info_outline),
                label: const Text("SMART"),
                onPressed: () async {
                  // show loader
                  showDialog(
                    context: context,
                    barrierDismissible: false,
                    builder: (_) =>
                        const Center(child: CircularProgressIndicator()),
                  );

                  try {
                    final smart = await storage.smartInfo(dev);
                    if (!context.mounted) return;
                    Navigator.pop(context); // remove loader

                    if (smart == null) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                            content: Text("Unable to fetch SMART info")),
                      );
                      return;
                    }

                    // callback or default bottom sheet
                    if (onSmart != null) {
                      onSmart!(smart);
                    } else {
                      _showSmartSheet(context, smart);
                    }
                  } catch (e) {
                    if (Navigator.canPop(context)) Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text("SMART error: $e")));
                  }
                },
              ),
              const SizedBox(height: 6),
              PopupMenuButton<String>(
                onSelected: (v) {
                  if (v == 'wipe') {
                    _showWipeDialog(context, storage, dev);
                  } else if (v == 'identify') {
                    // optional identify
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                        content: Text('Identify not implemented')));
                  }
                },
                itemBuilder: (_) => [
                  const PopupMenuItem(
                      value: 'wipe',
                      child: Text('Wipe Disk',
                          style: TextStyle(color: Colors.red))),
                  const PopupMenuItem(
                      value: 'identify', child: Text('Identify (blink)')),
                ],
              ),
            ],
          ),
        ]),
      ),
    );
  }

  void _showSmartSheet(BuildContext ctx, Map<String, dynamic> smart) {
    showModalBottomSheet(
      context: ctx,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(12))),
      builder: (c) {
        final attrs = smart['attributes'] as List? ?? [];
        return Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                    child: Text('SMART: ${smart['model'] ?? _devpath()}',
                        style: const TextStyle(
                            fontWeight: FontWeight.bold, fontSize: 18))),
                const SizedBox(height: 8),
                Text('Serial: ${smart['serial'] ?? '-'}'),
                Text('Health: ${smart['health'] ?? '-'}'),
                Text('Temp: ${smart['temp'] ?? '-'}'),
                const SizedBox(height: 12),
                const Text('Attributes',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                SizedBox(
                  height: 300,
                  child: ListView.builder(
                    itemCount: attrs.length,
                    itemBuilder: (_, i) {
                      final a = attrs[i];
                      return ListTile(
                        dense: true,
                        title: Text(a['name'] ?? a['id'].toString()),
                        subtitle: Text('Raw: ${a['raw'] ?? '-'}'),
                        trailing: Text('${a['value'] ?? '-'}'),
                      );
                    },
                  ),
                ),
              ]),
        );
      },
    );
  }

  void _showWipeDialog(
      BuildContext ctx, StorageProvider storage, String devpath) {
    final mode = ValueNotifier<String>('quick');
    final confirm = TextEditingController();

    showDialog(
      context: ctx,
      builder: (_) => AlertDialog(
        title: Row(children: const [
          Icon(Icons.warning, color: Colors.red),
          SizedBox(width: 8),
          Text('Wipe Disk')
        ]),
        content: StatefulBuilder(builder: (context, setState) {
          return SingleChildScrollView(
            child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('You are about to wipe: $devpath',
                      style: const TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  RadioListTile<String>(
                      value: 'quick',
                      groupValue: mode.value,
                      title: const Text('Quick (zap partitions + wipefs)'),
                      onChanged: (v) => mode.value = v ?? 'quick'),
                  RadioListTile<String>(
                      value: 'zero',
                      groupValue: mode.value,
                      title: const Text('Zero (overwrite beginning)'),
                      onChanged: (v) => mode.value = v ?? 'zero'),
                  RadioListTile<String>(
                      value: 'random',
                      groupValue: mode.value,
                      title: const Text('Random (shred)'),
                      onChanged: (v) => mode.value = v ?? 'random'),
                  const SizedBox(height: 8),
                  TextField(
                      controller: confirm,
                      decoration: InputDecoration(
                          labelText: 'Type device to confirm',
                          hintText: devpath)),
                  const SizedBox(height: 8),
                  const Text('This is destructive. Data will be lost.',
                      style: TextStyle(color: Colors.red)),
                ]),
          );
        }),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () async {
              if (confirm.text.trim() != devpath) {
                ScaffoldMessenger.of(ctx).showSnackBar(const SnackBar(
                    content: Text('Confirmation does not match device path')));
                return;
              }
              Navigator.pop(ctx); // close dialog
              // show progress modal
              showDialog(
                  context: ctx,
                  barrierDismissible: false,
                  builder: (_) =>
                      const Center(child: CircularProgressIndicator()));
              try {
                final res = await storage.wipeDisk(devpath, mode.value);
                if (!ctx.mounted) return;
                Navigator.pop(ctx); // close progress
                if (res['ok'] == true) {
                  ScaffoldMessenger.of(ctx).showSnackBar(
                      const SnackBar(content: Text('Wipe started')));
                } else {
                  ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(
                      content: Text(
                          'Wipe failed: ${res['error'] ?? res.toString()}')));
                }
              } catch (e) {
                if (Navigator.canPop(ctx)) Navigator.pop(ctx);
                ScaffoldMessenger.of(ctx)
                    .showSnackBar(SnackBar(content: Text('Wipe error: $e')));
              }
            },
            child: const Text('Wipe Disk'),
          ),
        ],
      ),
    );
  }
}
