import 'package:flutter/material.dart';
import '../services/api_service.dart';

class BackupProvider extends ChangeNotifier {
  final ApiService api;
  List<dynamic> backups = [];

  BackupProvider({ApiService? api}) : api = api ?? ApiService();

  Future<void> loadBackups() async {
    backups = await api.listBackups();
    notifyListeners();
  }

  Future<void> createBackup() async {
    await api.createBackup();
    await loadBackups();
  }

  Future<void> restore(String file) async {
    await api.restoreBackup(file);
    await loadBackups();
  }
}
