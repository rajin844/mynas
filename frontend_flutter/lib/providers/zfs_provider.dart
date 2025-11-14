import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ZfsProvider extends ChangeNotifier {
  final ApiService api;
  List<dynamic> pools = [];
  Map<String, List<dynamic>> datasets = {};

  ZfsProvider({ApiService? api}) : api = api ?? ApiService();

  Future<void> loadPools() async {
    try {
      pools = await api.listPools();
      notifyListeners();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> loadDatasets(String pool) async {
    try {
      final ds = await api.listDatasets(pool);
      datasets[pool] = List.from(ds);
      notifyListeners();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> createDataset(String pool, String name,
      {String? mountpoint}) async {
    await api.createDataset(pool, name, mountpoint: mountpoint);
    await loadDatasets(pool);
  }
}
