import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';

class SmartProvider extends ChangeNotifier {
  final ApiService api;
  final WebSocketService ws;
  List<dynamic> disks = [];
  bool loading = false;
  StreamSubscription? _sub;

  SmartProvider({ApiService? api, WebSocketService? ws})
      : api = api ?? ApiService(),
        ws = ws ?? WebSocketService() {
    _sub = this.ws.stream.listen((msg) {
      if (msg['module'] == 'smart' && msg['event'] == 'disk_update') {
        // refresh UI or update single disk entry
        refresh();
      }
    });
  }

  // SMART data per pool
  Map<String, List<Map<String, dynamic>>> poolSmart = {};

  Future<void> refresh() async {
    loading = true;
    notifyListeners();
    try {
      disks = await api.smartScanAll();
    } catch (_) {
      disks = [];
    }
    loading = false;
    notifyListeners();
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  // ============================
  // SMART for a POOL
  // ============================
  Future<void> loadSmartForPool(String pool) async {
    try {
      final res = await api.callRpc("smart", "listPoolSmart", {"pool": pool});
      if (res is List) {
        poolSmart[pool] = List<Map<String, dynamic>>.from(res);
      } else {
        poolSmart[pool] = [];
      }
    } catch (_) {
      poolSmart[pool] = [];
    }
    notifyListeners();
  }
}
