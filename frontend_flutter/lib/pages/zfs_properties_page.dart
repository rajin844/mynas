// lib/pages/zfs_properties_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/zfs_provider.dart';

class ZfsPropertiesPage extends StatefulWidget {
  final String dataset;
  const ZfsPropertiesPage({super.key, required this.dataset});
  @override
  State<ZfsPropertiesPage> createState() => _ZfsPropertiesPageState();
}

class _ZfsPropertiesPageState extends State<ZfsPropertiesPage> {
  Map<String, String> props = {};
  final kCtrl = TextEditingController();
  final vCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    // load props via provider -> zfs.pool properties rpc (implement if needed)
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Properties: ${widget.dataset}")),
      body: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(children: [
            Row(children: [
              Expanded(
                  child: TextField(
                      controller: kCtrl,
                      decoration:
                          const InputDecoration(labelText: "Property"))),
              const SizedBox(width: 8),
              Expanded(
                  child: TextField(
                      controller: vCtrl,
                      decoration: const InputDecoration(labelText: "Value"))),
              ElevatedButton(
                  onPressed: () async {
                    // call provider/api to set property
                    // context.read<ZfsProvider>().setProperty(widget.dataset, kCtrl.text.trim(), vCtrl.text.trim());
                    ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text("Set property (stub)")));
                  },
                  child: const Text("Set"))
            ]),
            const SizedBox(height: 12),
            const Text("Current properties (not loaded)"),
          ])),
    );
  }
}
