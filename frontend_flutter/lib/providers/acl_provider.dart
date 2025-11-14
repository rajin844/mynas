import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AclProvider extends ChangeNotifier {
  final ApiService api;
  Map<String, dynamic> acl = {};

  AclProvider({ApiService? api}) : api = api ?? ApiService();

  Future<void> loadAcl(String path) async {
    acl = await api.listAcl(path);
    notifyListeners();
  }

  Future<void> setAcl(String path, dynamic value) async {
    await api.setAcl(path, value);
    await loadAcl(path);
  }

  Future<void> removeAcl(String path) async {
    await api.removeAcl(path);
    acl = {};
    notifyListeners();
  }
}
