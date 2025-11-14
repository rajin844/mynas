import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  final String baseUrl;
  ApiService({String? baseUrl})
      : baseUrl = baseUrl ?? "http://${Uri.base.host}:8000";

  Future<dynamic> callRpc(
      String module, String method, Map<String, dynamic> params) async {
    final url = Uri.parse('$baseUrl/rpc');
    //final url = Uri.parse(
    //  '$baseUrl/api/${module.toLowerCase()}/${method.toLowerCase()}');
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(params),
    );

    if (response.statusCode == 200) {
      try {
        return jsonDecode(response.body);
      } catch (e) {
        return response.body;
      }
    }
    throw Exception(
        'API ${url.toString()} failed: ${response.statusCode} ${response.body}');
  }

  // convenience wrappers
  Future<List<dynamic>> listPools() async =>
      await callRpc("ZFS", "listPools", {});
  Future<List<dynamic>> listDatasets(String? pool) async =>
      await callRpc("ZFS", "listDatasets", {"pool": pool});
  Future<List<dynamic>> listShares() async =>
      await callRpc("SHARE", "listShares", {});
  Future<dynamic> createPool(String name, List<String> devices,
          {bool dryRun = true}) async =>
      await callRpc("STORAGE", "create_pool",
          {"name": name, "devices": devices, "dry_run": dryRun});
  Future<dynamic> createDataset(String pool, String name,
          {String? mountpoint, bool dryRun = true}) async =>
      await callRpc("ZFS", "createDataset", {
        "pool": pool,
        "name": name,
        "mountpoint": mountpoint,
        "dry_run": dryRun
      });
  Future<dynamic> createShare(
          String name, String path, String protocol) async =>
      await callRpc("SHARE", "createShare",
          {"name": name, "path": path, "protocol": protocol});
  Future<dynamic> deleteShare(String uuid) async =>
      await callRpc("SHARE", "deleteShare", {"uuid": uuid});
  Future<dynamic> listBackups() async => await callRpc("BACKUP", "list", {});
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
