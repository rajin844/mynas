import 'package:flutter/material.dart';
import 'package:frontend_flutter/services/websocket_service.dart';
import '../services/api_service.dart';

class DashboardScreen extends StatefulWidget {
  final ApiService api; // ✅ define api field
  const DashboardScreen({super.key, required this.api});
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  WebSocketService wsService = WebSocketService();
  final ApiService apiService = ApiService(baseUrl: "http://localhost:8000");
  List<Map<String, dynamic>> pools = [];
  List<Map<String, dynamic>> datasets = [];
  List<Map<String, dynamic>> shares = [];
  bool loading = true;
  String status = 'Waiting for server...';

  @override
  void initState() {
    super.initState();
    connectWebSocket();
    loadDashboardData();
  }

  void connectWebSocket() async {
    await wsService.connect("ws://localhost:6789");
    wsService.setListener((msg) {
      setState(() {
        status = "Event: ${msg['event']}";
      });
      if (msg['event'] == "dataset_created") {
        loadDashboardData();
      }
    });
  }

  Future<void> loadDashboardData() async {
    try {
      var poolResp = await apiService.callRpc("ZFS", "listPools", {});
      var datasetResp = await apiService.callRpc("ZFS", "listDatasets", {});
      var shareResp = await apiService.callRpc("SHARE", "listShares", {});

      if (poolResp is List) {
        pools = poolResp.map((e) => Map<String, dynamic>.from(e)).toList();
      }
      if (datasetResp is List) {
        datasets =
            datasetResp.map((e) => Map<String, dynamic>.from(e)).toList();
      }
      if (shareResp is List) {
        shares = shareResp.map((e) => Map<String, dynamic>.from(e)).toList();
      }
    } catch (e) {
      debugPrint("Error loading dashboard data: $e");
    }

    setState(() => loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("NAS Dashboard")),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: loadDashboardData,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildSection("ZFS Pools main", pools),
                    _buildSection("Datasets", datasets),
                    _buildSection("Shares", shares),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildSection(String title, List<Map<String, dynamic>> items) {
    return Card(
      margin: const EdgeInsets.only(bottom: 20),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title,
                style:
                    const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            ...items.map((item) => ListTile(
                  title: Text(item["name"] ?? "Unnamed"),
                  subtitle: Text(item.toString()),
                )),
          ],
        ),
      ),
    );
  }
}
