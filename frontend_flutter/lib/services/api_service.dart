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

  // convenience wrappers
  Future<List<dynamic>> listPools() async =>
      List.from(await callRpc("ZFS", "listPools", {}));
  Future<List<dynamic>> listDatasets(String? pool) async =>
      List.from(await callRpc("ZFS", "listDatasets", {"pool": pool}));
  Future<List<dynamic>> listShares() async =>
      List.from(await callRpc("SHARE", "listShares", {}));
  Future<dynamic> createPool(String name, List<String> devices,
          {bool dryRun = true}) async =>
      await callRpc("STORAGE", "create_pool",
          {"name": name, "devices": devices, "dry_run": dryRun});
  Future<dynamic> createDataset(String pool, String name,
          {String? mountpoint}) async =>
      await callRpc("ZFS", "createDataset",
          {"pool": pool, "name": name, "mountpoint": mountpoint});
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
  Future<dynamic> getMetrics() async => await callRpc("MONITOR", "metrics", {});
  Future<dynamic> listAcl(String path) async =>
      await callRpc("ACL", "getAcl", {"path": path});
  Future<dynamic> setAcl(String path, dynamic acl) async =>
      await callRpc("ACL", "setAcl", {"path": path, "acl": acl});
  Future<dynamic> removeAcl(String path) async =>
      await callRpc("ACL", "removeAcl", {"path": path});
}
