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
  Map<String, dynamic> vdevTopology = {};
  bool loadingPools = false;
  bool loadingDatasets = false;
  StreamSubscription? _sub;
  //List<Map<String, dynamic>> pools = [];
  Map<String, dynamic> poolDetails = {};
  Map<String, List<Map<String, dynamic>>> poolDatasets = {};

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

  // ================================
  // 💠 POOL DETAILS
  // ================================
  Future<Map<String, dynamic>> getPoolDetails(String name) async {
    try {
      final result = await api.callRpc("zfs", "poolDetails", {"pool": name});

      final pool = result is Map ? result : {};

      // Normalize
      poolDetails = {
        "name": pool["name"] ?? name,
        "health": pool["health"] ?? pool["status"] ?? "UNKNOWN",
        "size": pool["size"] ?? pool["capacity"] ?? pool["total"] ?? "0",
        "alloc": pool["alloc"] ?? pool["used"] ?? "0",
        "vdevs": List<Map<String, dynamic>>.from(
          pool["vdevs"] ?? pool["topology"] ?? pool["devices"] ?? [],
        ),
      };

      notifyListeners();
      return poolDetails;
    } catch (e) {
      return {};
    }
  }

  // ================================
  // 💠 DATASETS FOR POOL
  // ================================
  Future<List<Map<String, dynamic>>> listDatasetsForPool(String pool) async {
    try {
      final res = await api.callRpc("zfs", "listDatasets", {"pool": pool});
      final list = res is List ? res : [];
      poolDatasets[pool] = List<Map<String, dynamic>>.from(list);
      notifyListeners();
      return poolDatasets[pool]!;
    } catch (_) {
      return [];
    }
  }

  // ================================
  // 💠 CREATE DATASET
  // ================================
  Future<Future<List<Map<String, dynamic>>>> createDataset(
      String pool, String name,
      {String? mountpoint}) async {
    await api.callRpc("zfs", "createDataset", {
      "pool": pool,
      "name": name,
      if (mountpoint != null) "mountpoint": mountpoint
    });

    return listDatasetsForPool(pool);
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

  // -----------------------------
  // SCRUB CONTROL
  // -----------------------------
  Future<void> startScrub(String pool) async {
    await api.callRpc("zfs", "startScrub", {"pool": pool});
    await loadPools();
  }

  Future<void> stopScrub(String pool) async {
    await api.callRpc("zfs", "stopScrub", {"pool": pool});
    await loadPools();
  }

  Future<double?> getScrubProgress(String pool) async {
    final res = await api.callRpc("zfs", "scrubProgress", {"pool": pool});
    if (res is Map && res.containsKey("percent")) {
      return (res["percent"] as num).toDouble();
    }
    if (res is num) return res.toDouble();
    return 0;
  }

  // -----------------------------
  // GET SCRUB STATUS
  // -----------------------------
  Future<Map<String, dynamic>> getScrubStatus(String pool) async {
    final result = await api.callRpc("zfs", "scrubStatus", {"pool": pool});
    return Map<String, dynamic>.from(result);
  }

  Future<List<Map<String, dynamic>>> getScrubHistory(String pool) async {
    final res = await api.callRpc("zfs", "scrubHistory", {"pool": pool});
    if (res is List) {
      return List<Map<String, dynamic>>.from(res);
    }
    return [];
  }

  // dataset ops //required bool dryRun
  Future<bool> createDatasets(
    String pool,
    String name, {
    String? mountpoint,
    required bool dryRun,
  }) async {
    final res = await api.createDataset(pool, name, mountpoint: mountpoint);
    await loadAllDatasets();
    return true;
  }

  Future<void> loadTopology(String pool) async {
    final res = await api.callRpc("zfs", "vdevtopology", {"pool": pool});
    vdevTopology = res;
    notifyListeners();
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
