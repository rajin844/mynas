import 'package:flutter/material.dart';
import '../services/api_service.dart';

class PoolsScreen extends StatefulWidget {
  const PoolsScreen({super.key});

  @override
  State<PoolsScreen> createState() => _PoolsScreenState();
}

class _PoolsScreenState extends State<PoolsScreen> {
  final apiService = ApiService(baseUrl: 'http://localhost:8000');
  List pools = [];

  @override
  void initState() {
    super.initState();
    fetchPools();
  }

  Future<void> fetchPools() async {
    try {
      var data = await apiService.callRpc("ZFS", "listPools", {});
      setState(() => pools = data);
    } catch (e) {
      debugPrint("Error fetching pools: $e");
    }
  }

  Future<void> createPool(String name) async {
    try {
      await apiService.callRpc("ZFS", "createPool", {"name": name});
      fetchPools();
    } catch (e) {
      debugPrint("Error creating pool: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("ZFS Pools")),
      body: ListView(
        children: pools
            .map((pool) => ListTile(title: Text(pool.toString())))
            .toList(),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () =>
            createPool("pool_${DateTime.now().millisecondsSinceEpoch}"),
        child: const Icon(Icons.add),
      ),
    );
  }
}
