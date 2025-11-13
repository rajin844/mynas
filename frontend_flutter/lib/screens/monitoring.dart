// lib/screens/monitoring.dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class MonitoringScreen extends StatefulWidget {
  const MonitoringScreen({super.key});

  @override
  State<MonitoringScreen> createState() => _MonitoringScreenState();
}

class _MonitoringScreenState extends State<MonitoringScreen> {
  final api = ApiService(baseUrl: 'http://localhost:8000');
  Map metrics = {};

  @override
  void initState() {
    super.initState();
    fetchMetrics();
  }

  Future<void> fetchMetrics() async {
    try {
      final res = await api.callRpc('monitoring', 'metrics', {});
      if (res is Map) metrics = res;
      setState(() {});
    } catch (e, st) {
      debugPrint('Monitoring error: $e\n$st'); // or use logger}
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: AppBar(title: Text('Monitoring')),
        body: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Column(children: [
            Text('CPU: ${metrics['cpu'] ?? '-'}%'),
            Text('Memory: ${metrics['memory'] ?? '-'}%'),
            Text('Disk: ${metrics['disk'] ?? '-'}%'),
            ElevatedButton(onPressed: fetchMetrics, child: Text('Refresh'))
          ]),
        ));
  }
}
