// lib/services/websocket_service.dart
// Robust WebSocket client for Flutter (web + mobile)
// - auto host detection using Uri.base
// - uses ws or wss depending on scheme
// - reconnection with exponential backoff + jitter
// - Stream of incoming JSON messages
// - send() and dispose()
import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;

class WebSocketService {
  WebSocketChannel? _channel;
  final StreamController<dynamic> _incoming = StreamController.broadcast();
  Stream<dynamic> get stream => _incoming.stream;

  // connection state
  bool _connected = false;
  bool get connected => _connected;

  // reconnection params
  final int maxAttempts;
  final Duration baseDelay;
  final Duration maxDelay;
  int _attempt = 0;
  Timer? _reconnectTimer;

  WebSocketService({
    this.maxAttempts = 10,
    this.baseDelay = const Duration(seconds: 1),
    this.maxDelay = const Duration(seconds: 30),
  });

  /// compute ws URL from current browser URI
  String _buildUrl(int port, String path) {
    final host = Uri.base.host.isEmpty ? 'localhost' : Uri.base.host;
    final isSecure = Uri.base.scheme == 'https';
    final protocol = isSecure ? 'wss' : 'ws';
    return '$protocol://$host:$port$path';
  }

  Future<void> connect({int port = 6789, String path = '/ws'}) async {
    // ensure previous channel closed
    _disconnectInternal();

    final url = _buildUrl(port, path);
    _attempt = 0;
    _connectLoop(url);
  }

  void _connectLoop(String url) {
    if (_attempt > maxAttempts) {
      _incoming.add({'type': 'ws_error', 'error': 'max_retries_exceeded'});
      return;
    }

    _attempt += 1;
    try {
      _channel = WebSocketChannel.connect(Uri.parse(url));
      _connected = true;
      _incoming.add({'type': 'ws_open'});
      // reset attempts after success
      _attempt = 0;

      _channel!.stream.listen((message) {
        try {
          final decoded = jsonDecode(message);
          _incoming.add(decoded);
        } catch (e) {
          _incoming.add(message);
        }
      }, onDone: () {
        _connected = false;
        _incoming.add({'type': 'ws_closed'});
        _scheduleReconnect(url);
      }, onError: (err) {
        _connected = false;
        _incoming.add({'type': 'ws_error', 'error': err.toString()});
        _scheduleReconnect(url);
      });
    } catch (e) {
      _connected = false;
      _incoming.add({'type': 'ws_error', 'error': e.toString()});
      _scheduleReconnect(url);
    }
  }

  void _scheduleReconnect(String url) {
    // exponential backoff + jitter
    final attempt = _attempt;
    final backoffMs = (baseDelay.inMilliseconds * pow(2, max(0, attempt - 1)))
        .clamp(0, maxDelay.inMilliseconds);
    final jitter = Random().nextInt(500); // up to 500ms jitter
    final delay = Duration(milliseconds: backoffMs.toInt() + jitter);

    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(delay, () {
      _connectLoop(url);
    });
  }

  void send(dynamic obj) {
    if (_channel == null) {
      throw StateError('WebSocket not connected');
    }
    final payload = obj is String ? obj : jsonEncode(obj);
    _channel!.sink.add(payload);
  }

  /// graceful disconnect
  Future<void> disconnect() async {
    _reconnectTimer?.cancel();
    _reconnectTimer = null;
    if (_channel != null) {
      try {
        _channel!.sink.close(status.goingAway);
      } catch (_) {}
    }
    _disconnectInternal();
  }

  void _disconnectInternal() {
    try {
      _channel = null;
      _connected = false;
    } catch (_) {}
  }

  void dispose() {
    disconnect();
    _incoming.close();
  }
}
