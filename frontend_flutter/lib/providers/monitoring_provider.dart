import 'package:flutter/material.dart';
import '../services/api_service.dart';

class MonitoringProvider extends ChangeNotifier {
  final ApiService api;
  double cpu = 0;
  double ram = 0;
  double disk = 0;
  List<String> events = [];

  MonitoringProvider({ApiService? api}) : api = api ?? ApiService();

  Future<void> refresh() async {
    final res = await api.getMetrics();
    cpu = (res['cpu'] as num).toDouble();
    ram = (res['memory'] as num).toDouble();
    disk = (res['disk'] as num).toDouble();
    notifyListeners();
  }

  void addEvent(String s) {
    events.insert(0, s);
    if (events.length > 200) events.removeLast();
    notifyListeners();
  }
}
