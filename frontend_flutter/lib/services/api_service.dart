// lib/services/api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => message;
}

class ApiService {
  final String baseUrl; // e.g. http://192.168.1.32:8000/api
  ApiService({String? baseUrl})
      : baseUrl = baseUrl ?? "http://${Uri.base.host}:8000/api";

  // Generic RPC call (router: /api/rpc/{service}/{method})
  Future<dynamic> callRpc(
      String service, String method, Map<String, dynamic> params) async {
    final url = Uri.parse("$baseUrl/rpc/$service/$method");
    final resp = await http.post(url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(params));
    if (resp.statusCode >= 400) {
      throw ApiException(
          "RPC $service/$method failed: ${resp.statusCode} ${resp.body}");
    }
    final data = jsonDecode(resp.body);
    if (data is Map && data["error"] != null) {
      throw ApiException(data["error"].toString());
    }
    return data["response"] ?? data;
  }

  // Generic REST POST helper (path starts with '/storage', '/zfs' etc)
  Future<dynamic> _post(String path, Map<String, dynamic>? payload) async {
    final url = Uri.parse("$baseUrl$path");
    final resp = await http.post(url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(payload ?? {}));
    if (resp.statusCode >= 400) {
      throw ApiException("API $path failed: ${resp.statusCode} ${resp.body}");
    }
    final data = jsonDecode(resp.body);
    if (data is Map && data["error"] != null) {
      throw ApiException(data["error"].toString());
    }
    return data["response"] ?? data;
  }

  // ----------------- Storage REST -----------------
  Future<List<dynamic>> listDisks() async =>
      List.from(await _post("/storage/listdisks", {}));
  Future<dynamic> detectDisks() async => await callRpc("storage", "detect", {});

  Future<Map<String, dynamic>> storageSummary() async =>
      Map.from(await _post("/storage/summary", {}));
  Future<dynamic> diskUsage(String dev) async =>
      await callRpc("storage", "disk_usage", {"dev": dev});
  Future<dynamic> smartInfo(String dev) async =>
      await callRpc("storage", "smart_info", {"dev": dev});
  Future<dynamic> createPoolRest(String name, List<String> devices,
          {String? raidz, bool dryRun = true, bool force = false}) =>
      _post("/storage/createpool", {
        "name": name,
        "devices": devices,
        "raidz": raidz,
        "dryRun": dryRun,
        "force": force
      });
  Future<dynamic> destroyPoolRest(String name) =>
      _post("/storage/destroypool", {"name": name});

  // ----------------- ZFS REST -----------------
  Future<List<dynamic>> listPools() async =>
      List.from(await _post("/zfs/listpools", {}));
  Future<List<dynamic>> listDatasets({String? pool}) async => List.from(
      await _post("/zfs/listdatasets", pool == null ? {} : {"pool": pool}));
  Future<dynamic> createDataset(String pool, String name,
          {String? mountpoint}) async =>
      await _post("/zfs/createdataset",
          {"pool": pool, "name": name, "mountpoint": mountpoint});
  Future<dynamic> destroyDataset(String pool, String name) async =>
      await _post("/zfs/destroydataset", {"pool": pool, "name": name});

  // ----------------- SMART -----------------
  Future<List<dynamic>> smartScanAll() async =>
      List.from(await _post("/smart/scan", {}));
  Future<dynamic> smartScanDisk(String devpath) async =>
      await _post("/smart/scan/disk", {"devpath": devpath});

  // ----------------- RAIDZ -----------------
  Future<dynamic> raidzPreview(List<String> devices, String mode) async =>
      await _post("/raidz/preview", {"devices": devices, "mode": mode});

  // ----------------- SHARES -----------------
  Future<List<dynamic>> listShares() async =>
      List.from(await _post("/shares/list", {}));
  Future<dynamic> createShare(
          String name, String path, String protocol) async =>
      await _post(
          "/shares/create", {"name": name, "path": path, "protocol": protocol});
  Future<dynamic> deleteShare(String name) async =>
      await _post("/shares/delete", {"name": name});

  // ----------------- BACKUP (REST or RPC depending on backend) -----------------
  Future<List<dynamic>> listBackups() async {
    // try REST first, fall back to RPC
    try {
      return List.from(await _post("/backup/list", {}));
    } catch (_) {
      return List.from(await callRpc("backup", "list", {}));
    }
  }

  Future<dynamic> createBackup() async {
    try {
      return await _post("/backup/create", {});
    } catch (_) {
      return await callRpc("backup", "create", {});
    }
  }

  Future<dynamic> restoreBackup(String file) async {
    try {
      return await _post("/backup/restore", {"file": file});
    } catch (_) {
      return await callRpc("backup", "restore", {"file": file});
    }
  }

  // ----------------- NETWORK -----------------
  Future<List<dynamic>> listInterfaces() async {
    try {
      return List.from(await _post("/network/listinterfaces", {}));
    } catch (_) {
      return List.from(await callRpc("network", "listInterfaces", {}));
    }
  }

  Future<List<dynamic>> getStorageAlerts() async {
    final res = await _post("/api/storage/alerts", {});
    return List.from(res["response"] ?? []);
  }

  // ----------------- USERS & ACL (RPC) -----------------
  Future<List<dynamic>> listUsers() async =>
      List.from(await callRpc("users", "list", {}));
  Future<dynamic> addUser(
          String username, String password, String role) async =>
      await callRpc("users", "add",
          {"username": username, "password": password, "role": role});
  Future<dynamic> removeUser(String username) async =>
      await callRpc("users", "remove", {"username": username});

  Future<dynamic> listAcl(String path) async =>
      await callRpc("acl", "getacl", {"path": path});
  Future<dynamic> setAcl(String path, dynamic acl) async =>
      await callRpc("acl", "setacl", {"path": path, "acl": acl});
  Future<dynamic> removeAcl(String path) async =>
      await callRpc("acl", "removeacl", {"path": path});

  // ----------------- MONITOR (RPC) -----------------
  Future<dynamic> getMetrics() async => await callRpc("monitor", "metrics", {});
  Future<dynamic> getHistory(String period) async =>
      await callRpc("monitor", "history", {"period": period});
}
