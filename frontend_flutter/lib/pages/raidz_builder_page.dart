import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/raidz_provider.dart';

class RaidzBuilderPage extends StatefulWidget {
  const RaidzBuilderPage({super.key});

  @override
  State<RaidzBuilderPage> createState() => _RaidzBuilderPageState();
}

class _RaidzBuilderPageState extends State<RaidzBuilderPage> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => context.read<RaidzProvider>().loadAvailableDisks());
  }

  @override
  Widget build(BuildContext context) {
    final p = context.watch<RaidzProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('RAIDZ Builder')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          Row(children: [
            Expanded(child: _buildDiskPicker(p)),
            const SizedBox(width: 12),
            Expanded(child: _buildControls(p)),
          ]),
          const SizedBox(height: 16),
          _buildPreviewCard(p),
          const SizedBox(height: 12),
          Row(
            children: [
              ElevatedButton.icon(
                onPressed:
                    p.selectedDisks.length < 1 ? null : () => p.previewLayout(),
                icon: const Icon(Icons.visibility),
                label: const Text('Preview (Dry-run)'),
              ),
              const SizedBox(width: 12),
              ElevatedButton.icon(
                onPressed:
                    p.canCreate ? () => _confirmCreate(context, p) : null,
                icon: const Icon(Icons.playlist_add_check),
                label: const Text('Create Pool'),
              ),
              const SizedBox(width: 12),
              OutlinedButton(
                onPressed: () => p.resetSelection(),
                child: const Text('Reset'),
              ),
            ],
          )
        ]),
      ),
    );
  }

  Widget _buildDiskPicker(RaidzProvider p) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Available Disks',
              style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Expanded(
            child: ListView.builder(
              itemCount: p.availableDisks.length,
              itemBuilder: (ctx, i) {
                final d = p.availableDisks[i];
                final selected = p.selectedDisks.contains(d);
                return CheckboxListTile(
                  value: selected,
                  onChanged: (v) => p.toggleDisk(d),
                  title: Text('${d["name"]} — ${d["size"]}'),
                  subtitle: Text('${d["model"] ?? ""} • ${d["vendor"] ?? ""}'),
                  secondary: Icon(
                      d['rotational'] == true ? Icons.storage : Icons.memory),
                );
              },
            ),
          ),
          const SizedBox(height: 8),
          Text('Selected: ${p.selectedDisks.length}',
              style: const TextStyle(fontWeight: FontWeight.w600)),
        ]),
      ),
    );
  }

  Widget _buildControls(RaidzProvider p) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Configuration',
              style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          TextField(
            controller: p.poolNameController,
            decoration: const InputDecoration(labelText: 'Pool name'),
          ),
          const SizedBox(height: 10),
          DropdownButtonFormField<String>(
            value: p.layout,
            items: const [
              DropdownMenuItem(value: 'single', child: Text('Single')),
              DropdownMenuItem(value: 'mirror', child: Text('Mirror')),
              DropdownMenuItem(value: 'raidz1', child: Text('RAIDZ1')),
              DropdownMenuItem(value: 'raidz2', child: Text('RAIDZ2')),
              DropdownMenuItem(value: 'raidz3', child: Text('RAIDZ3')),
            ],
            onChanged: (v) => p.setLayout(v ?? 'single'),
            decoration: const InputDecoration(labelText: 'Target layout'),
          ),
          const SizedBox(height: 10),
          SwitchListTile(
            title: const Text('Dry-run (default)'),
            subtitle: const Text(
                'When enabled, the server will only return a preview'),
            value: p.dryRun,
            onChanged: (v) => p.setDryRun(v),
          ),
          const SizedBox(height: 8),
          ElevatedButton.icon(
            onPressed: () => p.autoLayoutSuggested(),
            icon: const Icon(Icons.auto_mode),
            label: const Text('Auto-layout (suggest)'),
          ),
        ]),
      ),
    );
  }

  Widget _buildPreviewCard(RaidzProvider p) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Layout Preview',
              style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          if (p.preview == null)
            const Text('No preview yet. Click "Preview (Dry-run)".')
          else ...[
            Text('Type: ${p.preview!["layout"]}'),
            const SizedBox(height: 6),
            Text('VDEV count: ${p.preview!["vdev_count"]}'),
            Text('Total usable capacity: ${p.preview!["usable_capacity"]}'),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: (p.preview!['vdevs'] as List<dynamic>).map((vdev) {
                return Chip(
                  avatar: const Icon(Icons.device_hub),
                  label: Text(vdev.join(', ')),
                );
              }).toList(),
            ),
            const SizedBox(height: 8),
            if (p.preview!['warnings'] != null)
              Text('Warnings: ${p.preview!['warnings'].join("; ")}',
                  style: const TextStyle(color: Colors.orange)),
          ]
        ]),
      ),
    );
  }

  Future<void> _confirmCreate(BuildContext ctx, RaidzProvider p) async {
    final ok = await showDialog<bool>(
      context: ctx,
      builder: (_) => AlertDialog(
        title: const Text('Confirm Create Pool'),
        content: Text(
            'Create pool "${p.poolNameController.text}" with layout ${p.layout}?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel')),
          ElevatedButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Create')),
        ],
      ),
    );

    if (ok == true) {
      await p.createPool();
      if (p.lastResult != null) {
        ScaffoldMessenger.of(ctx).showSnackBar(
            SnackBar(content: Text('Create result: ${p.lastResult!}')));
      }
    }
  }
}
