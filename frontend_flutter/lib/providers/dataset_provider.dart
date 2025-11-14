// lib/providers/dataset_provider.dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';

class DatasetProvider extends ChangeNotifier {
  final ApiService api;
  final WebSocketService ws;
  List<dynamic> datasets = [];
  bool loading = false;

  DatasetProvider({required this.api, required this.ws}) {
    fetchDatasets();
  }

  Future<void> fetchDatasets() async {
    loading = true;
    notifyListeners();
    try {
      final res = await api.callRpc('ZFS', 'listDatasets', {});
      if (res is List) {
        datasets = res;
      } else if (res is Map && res.containsKey('datasets')) {
        datasets = List.from(res['datasets']);
      }
    } catch (e) {
      datasets = [];
    }
    loading = false;
    notifyListeners();
  }

  Future<void> createDataset(String name) async {
    await api.callRpc('ZFS', 'createDataset', {'name': name});
    ws.send({'event': 'dataset_created', 'dataset': name});
    await fetchDatasets();
  }

  Future<void> deleteDataset(String name) async {
    await api.callRpc('ZFS', 'deleteDataset', {'name': name});
    ws.send({'event': 'dataset_deleted', 'dataset': name});
    datasets.removeWhere((d) => (d is Map && d['name'] == name) || d == name);
    notifyListeners();
  }
}
