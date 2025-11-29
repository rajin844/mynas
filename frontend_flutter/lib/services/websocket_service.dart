import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

/// ---------------------------------------------------------------------------
///  WebSocketService (MyNAS)
///  - Auto reconnect (exponential backoff + jitter)
///  - Auto JSON decode
///  - Auto subscribe to modules: monitor, zfs, storage, shares
///  - Dispatches events to Provider layer
/// ---------------------------------------------------------------------------
class WebSocketService extends ChangeNotifier {
  WebSocketChannel? _channel;
  bool _connected = false;
  bool get connected => _connected;

  final _incoming = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get stream => _incoming.stream;

  Timer? _reconnectTimer;
  int _attempt = 0;

  /// CONFIG
  final int maxAttempts;
  final Duration baseDelay;
  final Duration maxDelay;
  final String wsPath;
  final int wsPort;

  WebSocketService({
    this.maxAttempts = 50,
    this.baseDelay = const Duration(seconds: 1),
    this.maxDelay = const Duration(seconds: 30),
    this.wsPath = "/ws",
    //this.wsPort = 8000,
    this.wsPort = 6789, // << FIXED
  });

  // ---------------------------------------------------------------------------
  //  Build ws:// URL dynamically (supports LAN + Flutter Web)
  // ---------------------------------------------------------------------------
  String _buildUrl() {
    final host = Uri.base.host.isEmpty ? "localhost" : Uri.base.host;
    final protocol = Uri.base.scheme == "https" ? "wss" : "ws";
    return "$protocol://$host:$wsPort$wsPath";
  }

  // ---------------------------------------------------------------------------
  //  Public connect() entry
  // ---------------------------------------------------------------------------
  Future<void> connect() async {
    _disconnectInternal();
    _attempt = 0;
    _tryConnect();
  }

  // ---------------------------------------------------------------------------
  //  Connect loop with retries
  // ---------------------------------------------------------------------------
  void _tryConnect() {
    final url = _buildUrl();
    if (_attempt > maxAttempts) {
      debugPrint("❌ WS max attempts reached");
      return;
    }

    _attempt++;
    debugPrint("🔌 WS Connect attempt $_attempt → $url");

    try {
      _channel = WebSocketChannel.connect(Uri.parse(url));

      _connected = true;
      notifyListeners();

      // Reset attempt counter after success
      _attempt = 0;

      // Listen stream
      _channel!.stream.listen(
        (raw) => _handleIncoming(raw),
        onError: (err) {
          debugPrint("❌ WS error: $err");
          _connected = false;
          notifyListeners();
          _scheduleReconnect();
        },
        onDone: () {
          debugPrint("⚠️ WS closed");
          _connected = false;
          notifyListeners();
          _scheduleReconnect();
        },
      );

      // Auto-subscribe to backend modules
      _autoSubscribe();
    } catch (e) {
      debugPrint("❌ WS immediate connect error: $e");
      _connected = false;
      notifyListeners();
      _scheduleReconnect();
    }
  }

  // ---------------------------------------------------------------------------
  //  Auto-subscribe to modules
  // ---------------------------------------------------------------------------
  void _autoSubscribe() {
    send({
      "action": "subscribe",
      "modules": ["monitor", "zfs", "storage", "shares"]
    });
  }

  // ---------------------------------------------------------------------------
  //  Handle incoming messages
  // ---------------------------------------------------------------------------
  void _handleIncoming(dynamic raw) {
    try {
      final decoded = raw is String ? jsonDecode(raw) : raw;
      if (decoded is Map<String, dynamic>) {
        _incoming.add(decoded);
      }
    } catch (_) {
      debugPrint("⚠️ WS non-JSON message ignored: $raw");
    }
  }

  // ---------------------------------------------------------------------------
  //  Send command / message
  // ---------------------------------------------------------------------------
  void send(dynamic msg) {
    if (_channel == null) return;

    final payload = msg is String ? msg : jsonEncode(msg);
    _channel!.sink.add(payload);
  }

  // ---------------------------------------------------------------------------
  //  Reconnect scheduler (exp-backoff + jitter)
  // ---------------------------------------------------------------------------
  void _scheduleReconnect() {
    if (_reconnectTimer != null) return;

    final base = baseDelay.inMilliseconds;
    final delay = min(maxDelay.inMilliseconds, base * pow(2, _attempt));
    final jitter = Random().nextInt(500);

    final total = Duration(milliseconds: delay.toInt() + jitter);

    debugPrint("⏳ WS reconnect in ${total.inMilliseconds}ms...");

    _reconnectTimer = Timer(total, () {
      _reconnectTimer = null;
      _tryConnect();
    });
  }

  // ---------------------------------------------------------------------------
  //  Manual disconnect
  // ---------------------------------------------------------------------------
  Future<void> disconnect() async {
    _reconnectTimer?.cancel();
    _reconnectTimer = null;

    try {
      await _channel?.sink.close();
    } catch (_) {}

    _disconnectInternal();
  }

  void _disconnectInternal() {
    _channel = null;
    _connected = false;
    notifyListeners();
  }

  // ---------------------------------------------------------------------------
  //  Cleanup
  // ---------------------------------------------------------------------------
  @override
  void dispose() {
    disconnect();
    _incoming.close();
    super.dispose();
  }
}
