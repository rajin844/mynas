// lib/pages/monitoring_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/monitoring_provider.dart';

class MonitoringPage extends StatelessWidget {
  const MonitoringPage({super.key});
  @override
  Widget build(BuildContext context) {
    final m = context.watch<MonitoringProvider>();
    return Scaffold(
      appBar: AppBar(title: const Text('Monitoring')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(children: [
          Text('CPU: ${m.cpu}%'),
          Text('RAM: ${m.ram}%'),
          Text('Disk: ${m.disk}%'),
          const SizedBox(height: 12),
          ElevatedButton(
              onPressed: () => m.refresh(), child: const Text('Refresh')),
        ]),
      ),
    );
  }
}
