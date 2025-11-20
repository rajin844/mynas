import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  final String baseUrl;
  ApiService({String? baseUrl})
      : baseUrl = baseUrl ?? "http://${Uri.base.host}:8000";

  Future<dynamic> callRpc(
      String service, String method, Map<String, dynamic> params) async {
    // final url = Uri.parse('$baseUrl/api');
    final url = Uri.parse(
        '$baseUrl/api/${service.toLowerCase()}/${method.toLowerCase()}');

    final payload = {"service": service, "method": method, "params": params};

    final resp = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(payload),
    );

    if (resp.statusCode != 200) {
      throw Exception(
          'API ${url.toString()} failed: ${resp.statusCode} ${resp.body}');
    }

    final data = jsonDecode(resp.body);
    if (data["error"] != null) {
      throw Exception("RPC error: ${data["error"]}");
    }
    return data["response"];
  }

  // Storage
  Future<List<dynamic>> listDisks() async =>
      List.from(await callRpc("STORAGE", "listDisks", {}));
  Future<dynamic> detectDisks() async =>
      await callRpc("STORAGE", "detectDisks", {});
  Future<dynamic> storageSummary() async =>
      await callRpc("STORAGE", "summary", {});
  Future<dynamic> rescanSata() async =>
      await callRpc("STORAGE", "rescanSata", {});
// ZFS
  Future<List<dynamic>> listPools() async =>
      List.from(await callRpc("ZFS", "listpools", {}));
  Future<dynamic> poolStatus(String pool) async =>
      await callRpc("ZFS", "poolStatus", {"pool": pool});

  Future<dynamic> createPool(
    String name,
    List<String> devices, {
    String? raidz,
    bool force = false,
    bool dryRun = true,
  }) async {
    return await callRpc("ZFS", "createPool", {
      "name": name,
      "devices": devices,
      "raidz": raidz,
      "force": force,
      "dry_run": dryRun,
    });
  }

  Future<dynamic> destroyPool(String name, {bool force = false}) async =>
      await callRpc("ZFS", "destroyPool", {"name": name, "force": force});

  Future<List<dynamic>> listDatasets({String? pool}) async =>
      List.from(await callRpc("ZFS", "listdatasets", {"pool": pool}));

  Future<dynamic> createDataset(String pool, String name,
          {String? mountpoint}) async =>
      await callRpc("ZFS", "createdataset",
          {"pool": pool, "name": name, "mountpoint": mountpoint});

  Future<dynamic> destroyDataset(String pool, String name,
          {bool recursive = false}) async =>
      await callRpc("ZFS", "destroydataset",
          {"pool": pool, "name": name, "recursive": recursive});

  Future<dynamic> importPool(String name, {String? path}) async =>
      await callRpc("ZFS", "importPool", {"name": name, "path": path});
  Future<dynamic> exportPool(String name) async =>
      await callRpc("ZFS", "exportPool", {"name": name});

  Future<dynamic> scrubPool(String name) async =>
      await callRpc("ZFS", "scrubPool", {"name": name});

  Future<List<dynamic>> listShares() async =>
      List.from(await callRpc("share", "list", {}));
  Future<dynamic> createShare(
          String name, String path, String protocol) async =>
      await callRpc("SHARE", "createShare",
          {"name": name, "path": path, "protocol": protocol});
  Future<dynamic> deleteShare(String uuid) async =>
      await callRpc("SHARE", "deleteShare", {"uuid": uuid});

  Future<List<dynamic>> listBackups() async =>
      List.from(await callRpc("BACKUP", "list", {}));
  Future<dynamic> createBackup() async => await callRpc("BACKUP", "create", {});
  Future<dynamic> restoreBackup(String file) async =>
      await callRpc("BACKUP", "restore", {"file": file});
  Future<dynamic> listInterfaces() async =>
      await callRpc("NETWORK", "listInterfaces", {});

  Future<dynamic> getMetrics() async => await callRpc("monitor", "metrics", {});

  Future<List<dynamic>> listAcl(String path) async =>
      await callRpc("ACL", "getAcl", {"path": path});

  Future<dynamic> setAcl(String path, List<Map<String, dynamic>> acl) async =>
      await callRpc("ACL", "setAcl", {"path": path, "acl": acl});

  Future<dynamic> removeAcl(String path) async =>
      await callRpc("ACL", "removeAcl", {"path": path});

  Future<List<dynamic>> listUsers() async =>
      List.from(await callRpc("USERS", "listUsers", {}));

  // inside ApiService class

// Raidz builder endpoints via RPC (or REST fallback)
  Future<List<dynamic>> listAvailableDisks() async =>
      List.from(await callRpc("storage", "listdisks", {}));

  Future<dynamic> buildRaidzPreview(Map<String, dynamic> params) async =>
      await callRpc("raidz", "preview", params);

  Future<dynamic> createPoolFromRaidz(Map<String, dynamic> params) async =>
      await callRpc("raidz", "create", params);
}
