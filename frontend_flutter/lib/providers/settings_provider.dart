import 'package:flutter/material.dart';
import '../services/api_service.dart';

class SettingsProvider extends ChangeNotifier {
  final ApiService api;
  Map<String, dynamic> settings = {};

  SettingsProvider({ApiService? api}) : api = api ?? ApiService();

  Future<void> load() async {
    // using SYSTEM rpc
    settings = await api.callRpc("SYSTEM", "getSettings", {});
    notifyListeners();
  }

  Future<void> save(Map<String, dynamic> newSettings) async {
    await api.callRpc("SYSTEM", "setSettings", {"data": newSettings});
    await load();
  }
}
