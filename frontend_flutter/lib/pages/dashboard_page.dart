import 'package:flutter/material.dart';
import '../services/websocket_service.dart';
import '../services/api_service.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  final WebSocketService wsService = WebSocketService();
  final ApiService apiService = ApiService(baseUrl: "http://localhost:8000");

  String status = "Connecting to WebSocket...";
  int? datasets;
  int? pools;
  int? shares;

  bool isLoading = true;
  bool isConnected = false;

  @override
  void initState() {
    super.initState();
    _initDashboard();
  }

  Future<void> _initDashboard() async {
    try {
      await wsService.connect("ws://localhost:6789");

      setState(() {
        status = "Connected ✅";
        isConnected = true;
      });

      // ✅ WebSocket event handler
      wsService.event = (msg) {
        setState(() {
          status = "Event: ${msg['event'] ?? 'unknown'}";
        });
        _fetchSummary();
      };

      await _fetchSummary();
    } catch (e) {
      setState(() {
        status = "WebSocket error: $e";
        isConnected = false;
      });
    }
  }

  Future<void> _fetchSummary() async {
    setState(() => isLoading = true);

    try {
      var poolResp = await apiService.callRpc("ZFS", "listPools", {});
      var datasetResp = await apiService.callRpc("ZFS", "listDatasets", {});
      var shareResp = await apiService.callRpc("SHARE", "listShares", {});

      // 👇 Debug prints — check actual API structure
      debugPrint("PoolResp: $poolResp");
      debugPrint("DatasetResp: $datasetResp");
      debugPrint("ShareResp: $shareResp");

      // ✅ Automatically detect data structure
      setState(() {
        pools = (poolResp['pools'] ?? poolResp['response'] ?? poolResp ?? [])
            .length;
        datasets = (datasetResp['datasets'] ??
                datasetResp['response'] ??
                datasetResp ??
                [])
            .length;
        shares =
            (shareResp['shares'] ?? shareResp['response'] ?? shareResp ?? [])
                .length;

        status = "Updated at ${TimeOfDay.now().format(context)}";
      });
    } catch (e) {
      setState(() {
        status = "Error fetching data: $e";
      });
    } finally {
      setState(() => isLoading = false);
    }
  }

  @override
  void dispose() {
    wsService.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text("MyNAS Dashboard"),
        backgroundColor: Colors.blueAccent,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          children: [
            Row(
              children: [
                Icon(
                  isConnected ? Icons.circle : Icons.circle_outlined,
                  color: isConnected ? Colors.green : Colors.red,
                  size: 14,
                ),
                const SizedBox(width: 6),
                Text(
                  isConnected ? "Connected" : "Disconnected",
                  style: TextStyle(
                    color: isConnected ? Colors.green : Colors.red,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              status,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 10),
            Expanded(
              child: isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : RefreshIndicator(
                      onRefresh: _fetchSummary,
                      child: GridView.count(
                        crossAxisCount: 2,
                        padding: const EdgeInsets.all(12),
                        crossAxisSpacing: 10,
                        mainAxisSpacing: 10,
                        childAspectRatio: 1.2,
                        children: [
                          _buildCard("Pools", pools),
                          _buildCard("Datasets", datasets),
                          _buildCard("Shares", shares),
                        ],
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCard(String title, int? value) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 300),
        child: value == null
            ? const Center(child: CircularProgressIndicator())
            : Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    "$value",
                    key: ValueKey(value),
                    style: const TextStyle(
                      fontSize: 38,
                      fontWeight: FontWeight.bold,
                      color: Colors.blueAccent,
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}
