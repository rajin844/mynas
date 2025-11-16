import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';

class ZfsProvider extends ChangeNotifier {
  final ApiService api;
  final WebSocketService ws;

  List<dynamic> pools = [];
  List<dynamic> datasets = [];

  ZfsProvider({ApiService? api, WebSocketService? ws})
      : api = api ?? ApiService(),
        ws = ws ?? WebSocketService() {
    this.ws.stream.listen(_onWs);
  }

  Future<void> loadPools() async {
    pools = await api.listPools();
    notifyListeners();
  }

  Future<dynamic> previewPool(
    String name,
    List<String> devices, {
    String? raidz,
  }) async {
    return await api.createPool(
      name,
      devices,
      raidz: raidz,
      dryRun: true, // DRY RUN PREVIEW
      force: false,
    );
  }

  Future<void> createPool(
    String name,
    List<String> devices, {
    String? raidz,
  }) async {
    await api.createPool(
      name,
      devices,
      raidz: raidz,
      dryRun: false, // REAL CREATION
      force: false,
    );
    await loadPools();
  }

  Future<void> loadAllDatasets() async {
    datasets = await api.listDatasets();
    notifyListeners();
  }

  Future<dynamic> poolStatus(String pool) async {
    return await api.poolStatus(pool);
  }

  Future<void> destroyPool(String name) async {
    await api.destroyPool(name);
    await loadPools();
  }

  Future<void> createDataset(String pool, String name,
      {String? mountpoint}) async {
    await api.createDataset(pool, name, mountpoint: mountpoint);
    await loadAllDatasets();
  }

  Future<void> destroyDataset(String pool, String name) async {
    await api.destroyDataset(pool, name);
    await loadAllDatasets();
  }

  Future<void> scrubPool(String pool) async {
    await api.scrubPool(pool);
  }

  void _onWs(dynamic msg) {
    if (msg is! Map) return;
    if (msg["module"] == "zfs") {
      loadPools();
      loadAllDatasets();
    }
  }
}
