import 'package:flutter/material.dart';
import '../services/api_service.dart';

class MonitoringProvider extends ChangeNotifier {
  final ApiService api;

  double cpu = 0;
  double ram = 0;
  double disk = 0;
  double netUp = 0;
  double netDown = 0;

  MonitoringProvider({ApiService? api}) : api = api ?? ApiService();

  // ---------------------------------------------------------------------------
  // REST: Manual metrics refresh
  // ---------------------------------------------------------------------------
  Future<void> refresh() async {
    final metrics = await api.getMetrics();

    cpu = _toDouble(metrics['cpu']);
    ram = _toDouble(metrics['memory']);
    disk = _toDouble(metrics['disk']);

    final net = metrics['network'] ?? {};
    netUp = _toDouble(net['upload_bps']);
    netDown = _toDouble(net['download_bps']);

    notifyListeners();
  }

  // ---------------------------------------------------------------------------
  // WebSocket: Automatic realtime update
  // ---------------------------------------------------------------------------
  void updateFromWs(Map<String, dynamic> data) {
    if (data.containsKey('cpu')) cpu = _toDouble(data['cpu']);
    if (data.containsKey('memory')) ram = _toDouble(data['memory']);
    if (data.containsKey('disk')) disk = _toDouble(data['disk']);

    if (data.containsKey('network')) {
      final net = data['network'] ?? {};
      netUp = _toDouble(net['upload_bps']);
      netDown = _toDouble(net['download_bps']);
    }

    notifyListeners();
  }

  // ---------------------------------------------------------------------------
  // Utility: Safe toDouble conversion
  // ---------------------------------------------------------------------------
  double _toDouble(dynamic v) {
    if (v == null) return 0;
    if (v is double) return v;
    if (v is int) return v.toDouble();
    if (v is String) return double.tryParse(v) ?? 0;
    return 0;
  }
}
