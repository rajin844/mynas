import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  final String baseUrl;
  ApiService({required this.baseUrl});

  Future<dynamic> callRpc(
      String module, String method, Map<String, dynamic> params) async {
    final url = Uri.parse(
        '$baseUrl/api/${module.toLowerCase()}/${method.toLowerCase()}');
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

  // Convenience wrappers if you prefer explicit endpoints
  Future<List<dynamic>> listDatasets() async {
    final res = await callRpc('ZFS', 'listDatasets', {});
    if (res is List) return res;
    if (res is Map && res.containsKey('datasets')) {
      return List.from(res['datasets']);
    }
    return [];
  }

  Future<List<dynamic>> listPools() async {
    final res = await callRpc('ZFS', 'listDatasets', {});
    if (res is List) return res;
    if (res is Map && res.containsKey('datasets')) {
      return List.from(res['datasets']);
    }
    return [];
  }

  Future<List<dynamic>> listShares() async {
    final res = await callRpc('ZFS', 'listDatasets', {});
    if (res is List) return res;
    if (res is Map && res.containsKey('datasets')) {
      return List.from(res['datasets']);
    }
    return [];
  }
}
