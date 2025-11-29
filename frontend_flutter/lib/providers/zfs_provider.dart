// lib/providers/zfs_provider.dart
import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';

class ZfsProvider extends ChangeNotifier {
  final ApiService api;
  final WebSocketService ws;
  List<dynamic> pools = [];
  List<dynamic> datasets = [];
  bool loadingPools = false;
  bool loadingDatasets = false;
  StreamSubscription? _sub;

  ZfsProvider({ApiService? api, WebSocketService? ws})
      : api = api ?? ApiService(),
        ws = ws ?? WebSocketService() {
    _sub = this.ws.stream.listen(_onWsEvent);
  }

  void _onWsEvent(Map<String, dynamic> msg) {
    if (msg['module'] != 'zfs') return;
    final event = msg['event'] ?? '';
    final data = msg['data'];
    // react to important events
    if (event.startsWith('pool.')) {
      loadPools();
    } else if (event.startsWith('dataset.')) {
      loadAllDatasets();
    } else if (event == 'pool.scrub_progress') {
      // optionally update specific pool info if provided
      loadPools();
    }
  }

  Future<void> loadPools() async {
    loadingPools = true;
    notifyListeners();
    try {
      pools = await api.listPools();
    } catch (_) {
      pools = [];
    }
    loadingPools = false;
    notifyListeners();
  }

  Future<void> loadAllDatasets() async {
    loadingDatasets = true;
    notifyListeners();
    try {
      datasets = await api.listDatasets();
    } catch (_) {
      datasets = [];
    }
    loadingDatasets = false;
    notifyListeners();
  }

  // Actions (RPC or REST depending on backend)
  Future<bool> createPool(String name, List<String> devices,
      {String? raidz, bool dryRun = true, bool force = false}) async {
    final res = await api.createPoolRest(name, devices,
        raidz: raidz, dryRun: dryRun, force: force);
    await loadPools();
    return res != null;
  }

  Future<Map?> previewPool(String name, List<String> devices,
      {String? raidz}) async {
    try {
      // REST preview uses storage.createPool dryRun true or raidz.preview etc.
      final res = await api.raidzPreview(devices, raidz ?? 'single');
      return res;
    } catch (_) {
      return null;
    }
  }

  Future<bool> destroyPool(String name) async {
    final res = await api.destroyPoolRest(name);
    await loadPools();
    return res != null;
  }

  Future<Map> poolStatus(String name) async {
    // backend RPC maybe: zfs.poolStatus
    try {
      final r = await api.callRpc("zfs", "poolStatus", {"name": name});
      return Map.from(r ?? {});
    } catch (_) {
      return {};
    }
  }

  Future<bool> scrubPool(String name) async {
    try {
      final r = await api.callRpc("zfs", "scrubPool", {"name": name});
      return r?["started"] == true;
    } catch (_) {
      return false;
    }
  }

  // dataset ops
  Future<bool> createDataset(String pool, String name,
      {String? mountpoint, required bool dryRun}) async {
    final res = await api.createDataset(pool, name, mountpoint: mountpoint);
    await loadAllDatasets();
    return true;
  }

  Future<bool> destroyDataset(String pool, String name) async {
    final res = await api.destroyDataset(pool, name);
    await loadAllDatasets();
    return true;
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}
