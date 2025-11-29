// lib/providers/backup_provider.dart
import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';

class BackupProvider extends ChangeNotifier {
  final ApiService api;
  final WebSocketService ws;
  List<dynamic> backups = [];
  StreamSubscription? _sub;

  BackupProvider({ApiService? api, WebSocketService? ws})
      : api = api ?? ApiService(),
        ws = ws ?? WebSocketService() {
    _sub = this.ws.stream.listen(_onWs);
  }

  void _onWs(Map<String, dynamic> msg) {
    if (msg['module'] != 'backup') return;
    final ev = msg['event'] ?? '';
    if (ev == 'list.updated') loadBackups();
  }

  Future<void> loadBackups() async {
    try {
      backups = await api.listBackups();
    } catch (_) {
      backups = [];
    }
    notifyListeners();
  }

  Future<void> createBackup() async {
    await api.createBackup();
    await loadBackups();
  }

  Future<void> restoreBackup(String file) async {
    await api.restoreBackup(file);
    await loadBackups();
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  Future<void> restore(String string) async {}
}
