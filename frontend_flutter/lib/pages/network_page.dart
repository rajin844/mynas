// lib/pages/network_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/network_provider.dart';

class NetworkPage extends StatefulWidget {
  const NetworkPage({super.key});
  @override
  State<NetworkPage> createState() => _NetworkPageState();
}

class _NetworkPageState extends State<NetworkPage> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => context.read<NetworkProvider>().loadInterfaces());
  }

  @override
  Widget build(BuildContext context) {
    final np = context.watch<NetworkProvider>();
    return Scaffold(
      appBar: AppBar(title: const Text('Network')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: ListView(
          children: np.ifaces.entries
              .map((e) => Card(
                  child: ListTile(
                      title: Text(e.key), subtitle: Text(e.value.toString()))))
              .toList(),
        ),
      ),
    );
  }
}
