// lib/providers/raidz_provider.dart
import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';

class RaidzProvider extends ChangeNotifier {
  final ApiService api;
  final WebSocketService ws;
  List<dynamic> availableDisks = [];
  StreamSubscription? _sub;

  RaidzProvider({ApiService? api, WebSocketService? ws})
      : api = api ?? ApiService(),
        ws = ws ?? WebSocketService() {
    _sub = this.ws.stream.listen(_onWs);
  }

  void _onWs(Map<String, dynamic> msg) {
    if (msg['module'] != 'storage') return;
    final ev = msg['event'] ?? '';
    if (ev == 'disks.updated') {
      loadAvailableDisks();
    }
  }

  Future<void> loadAvailableDisks() async {
    try {
      availableDisks = await api.listDisks();
    } catch (_) {
      availableDisks = [];
    }
    notifyListeners();
  }

  Future<dynamic> previewRaidz(List<String> devices, String mode) async {
    return await api.raidzPreview(devices, mode);
  }

  Future<dynamic> createPoolFromRaidz(
      String name, List<String> devices, String mode,
      {bool dryRun = true}) async {
    return await api.createPoolRest(name, devices, raidz: mode, dryRun: dryRun);
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}
