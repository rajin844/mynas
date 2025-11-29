import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';

class StorageProvider extends ChangeNotifier {
  final ApiService api;
  final WebSocketService ws;
  List<dynamic> alerts = []; // <-- FIX ADDED
  List<dynamic> disks = [];
  Map<String, dynamic> summary = {};
  bool loading = false;
  StreamSubscription? _sub;

  StorageProvider({ApiService? api, WebSocketService? ws})
      : api = api ?? ApiService(),
        ws = ws ?? WebSocketService() {
    _sub = this.ws.stream.listen((msg) {
      try {
        if (msg['module'] == 'storage' && msg['event'] == 'summary_updated') {
          loadSummary();
        }
      } catch (_) {}
    });
  }

  Future<void> loadDisks() async {
    loading = true;
    notifyListeners();
    try {
      disks = await api.listDisks();
    } catch (_) {
      disks = [];
    }
    loading = false;
    notifyListeners();
  }

  Future<void> loadSummary() async {
    loading = true;
    notifyListeners();
    try {
      summary = await api.storageSummary();
    } catch (_) {
      summary = {};
    }
    loading = false;
    notifyListeners();
  }

  Future<dynamic> createPool(String name, List<String> devices,
      {String? raidz, bool dryRun = true, bool force = false}) async {
    final res = await api.createPoolRest(name, devices,
        raidz: raidz, dryRun: dryRun, force: force);
    if (!dryRun) {
      await loadSummary();
    }
    return res;
  }

  Future<dynamic> previewRaidz(List<String> devices, String mode) async {
    return await api.raidzPreview(devices, mode);
  }

  Future<dynamic> smartInfo(String dev) async {
    return await api.smartInfo(dev);
  }

  Future<dynamic> loadAlerts() async {
    return await api.getStorageAlerts();
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}
