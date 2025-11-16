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
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _metricTile(
              title: "CPU Usage",
              value: "${m.cpu.toStringAsFixed(1)}%",
              icon: Icons.memory,
              color: Colors.orange,
            ),
            _metricTile(
              title: "RAM Usage",
              value: "${m.ram.toStringAsFixed(1)}%",
              icon: Icons.storage,
              color: Colors.blue,
            ),
            _metricTile(
              title: "Disk Usage",
              value: "${m.disk.toStringAsFixed(1)}%",
              icon: Icons.storage,
              color: Colors.green,
            ),
            const SizedBox(height: 20),
            _networkTile(m),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => m.refresh(),
              child: const Text("Refresh (REST API)"),
            ),
          ],
        ),
      ),
    );
  }

  Widget _metricTile({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Card(
      child: ListTile(
        leading: Icon(icon, size: 32, color: color),
        title: Text(title),
        subtitle: LinearProgressIndicator(
          value: double.tryParse(value.replaceAll("%", ""))! / 100,
          color: color,
          backgroundColor: Colors.black12,
        ),
        trailing: Text(
          value,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  Widget _networkTile(MonitoringProvider m) {
    return Card(
      child: ListTile(
        leading:
            const Icon(Icons.network_check, size: 32, color: Colors.purple),
        title: const Text("Network Usage"),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Upload: ${_formatSpeed(m.netUp)}"),
            Text("Download: ${_formatSpeed(m.netDown)}"),
          ],
        ),
      ),
    );
  }

  String _formatSpeed(double bps) {
    if (bps < 1024) return "${bps.toStringAsFixed(0)} B/s";
    if (bps < 1024 * 1024) return "${(bps / 1024).toStringAsFixed(1)} KB/s";
    return "${(bps / 1024 / 1024).toStringAsFixed(2)} MB/s";
  }
}
