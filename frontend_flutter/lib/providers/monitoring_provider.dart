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

  // REST manual refresh
  Future<void> refresh() async {
    final metrics = await api.getMetrics(); // <-- no args required
    cpu = (metrics['cpu'] ?? 0).toDouble();
    ram = (metrics['memory'] ?? 0).toDouble();
    disk = (metrics['disk'] ?? 0).toDouble();
    netUp = (metrics['network']?['upload_bps'] ?? 0).toDouble();
    netDown = (metrics['network']?['download_bps'] ?? 0).toDouble();
    notifyListeners();
  }

  // WebSocket auto-update
  void updateFromWs(Map data) {
    cpu = (data['cpu'] ?? 0).toDouble();
    ram = (data['memory'] ?? 0).toDouble();
    disk = (data['disk'] ?? 0).toDouble();
    netUp = (data['network']?['upload_bps'] ?? 0).toDouble();
    netDown = (data['network']?['download_bps'] ?? 0).toDouble();
    notifyListeners();
  }
}
