import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';

class NetworkProvider extends ChangeNotifier {
  final ApiService api;
  final WebSocketService ws;

  Map<String, dynamic> interfaces = {};
  bool loading = false;

  NetworkProvider({
    required this.api,
    required this.ws,
  }) {
    // Subscribe to Network WS events
    ws.stream.listen((msg) {
      if (msg is Map && msg["module"] == "network") {
        if (msg["event"] == "update") {
          _handleWsUpdate(msg["data"]);
        }
      }
    });
  }

  // -------------------------------
  // LOAD INTERFACES
  // -------------------------------
  Future<void> loadInterfaces() async {
    loading = true;
    notifyListeners();

    try {
      final res = await api.callRpc("network", "listInterfaces", {});
      interfaces = Map<String, dynamic>.from(res ?? {});
    } catch (e) {
      interfaces = {};
    }

    loading = false;
    notifyListeners();
  }

  // -------------------------------
  // HANDLE WS EVENT
  // -------------------------------
  void _handleWsUpdate(dynamic data) {
    if (data is Map) {
      interfaces = Map<String, dynamic>.from(data);
      notifyListeners();
    }
  }

  // -------------------------------
  // SET STATIC IP
  // -------------------------------
  Future<bool> setStaticIP(
      String iface, String ip, String mask, String gw) async {
    final res = await api.callRpc("network", "setStatic", {
      "iface": iface,
      "ip": ip,
      "netmask": mask,
      "gateway": gw,
    });
    return res["ok"] == true;
  }

  // -------------------------------
  // ENABLE DHCP
  // -------------------------------
  Future<bool> enableDhcp(String iface) async {
    final res = await api.callRpc("network", "enableDhcp", {"iface": iface});
    return res["ok"] == true;
  }
}
