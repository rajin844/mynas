import 'package:flutter/material.dart';
import '../services/api_service.dart';

class SharesProvider extends ChangeNotifier {
  final ApiService api;
  List<dynamic> shares = [];

  SharesProvider({ApiService? api}) : api = api ?? ApiService();

  Future<void> loadShares() async {
    shares = await api.listShares();
    notifyListeners();
  }

  Future<void> createShare(String name, String path, String protocol) async {
    await api.createShare(name, path, protocol);
    await loadShares();
  }

  Future<void> deleteShare(String uuid) async {
    await api.deleteShare(uuid);
    await loadShares();
  }
}
