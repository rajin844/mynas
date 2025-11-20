import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';

class StorageProvider extends ChangeNotifier {
  final ApiService api;
  final WebSocketService ws;

  List<dynamic> disks = [];
  Map<String, dynamic>? summary;

  bool loadingDisks = false;
  bool loadingSummary = false;

  StorageProvider({ApiService? api, WebSocketService? ws})
      : api = api ?? ApiService(),
        ws = ws ?? WebSocketService() {
    // Listen for WS storage module events
    this.ws.stream.listen(_handleWs);
  }

  // ------------------------------
  // 🔄 Load Disks
  // ------------------------------
  Future<void> loadDisks() async {
    loadingDisks = true;
    notifyListeners();

    try {
      disks = await api.listDisks();
    } catch (e) {
      debugPrint("Error loading disks: $e");
    }

    loadingDisks = false;
    notifyListeners();
  }

  // ------------------------------
  // 🔄 Detect / Refresh Disks
  // ------------------------------
  Future<void> detectDisks() async {
    loadingDisks = true;
    notifyListeners();

    try {
      await api.detectDisks(); // backend also updates config + WS broadcast
      await loadDisks(); // refresh after detection
    } catch (e) {
      debugPrint("Disk detection error: $e");
    }

    loadingDisks = false;
    notifyListeners();
  }

  // ------------------------------
  // 🔁 SATA Rescan
  // ------------------------------
  Future<void> rescanSata() async {
    try {
      await api.rescanSata();
      await loadDisks();
    } catch (e) {
      debugPrint("SATA rescan failed: $e");
    }
  }

  // ------------------------------
  // 📊 Storage Summary
  // ------------------------------
  Future<void> loadSummary() async {
    loadingSummary = true;
    notifyListeners();

    try {
      summary = await api.storageSummary();
    } catch (e) {
      debugPrint("Error loading storage summary: $e");
    }

    loadingSummary = false;
    notifyListeners();
  }

  // ------------------------------
  // 🧭 WebSocket Handling
  // ------------------------------
  void _handleWs(dynamic msg) {
    if (msg is! Map) return;

    if (msg["module"] == "storage") {
      String event = msg["event"] ?? "";

      // Live updates
      if (event == "disks_detected") {
        loadDisks();
        loadSummary();
      }
    }
    //void _onWs(dynamic msg) {
    // if (msg is Map && msg["module"] == "storage") {
    //loadSummary();
    // loadDisks();
    // }
  }
}
