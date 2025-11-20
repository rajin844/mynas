import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketService extends ChangeNotifier {
  WebSocketChannel? _channel;
  bool _connected = false;
  bool get connected => _connected;

  final StreamController<dynamic> _incoming = StreamController.broadcast();
  Stream<dynamic> get stream => _incoming.stream;

  final int maxAttempts;
  final Duration baseDelay;
  final Duration maxDelay;
  int _attempt = 0;
  Timer? _reconnectTimer;
  final int apiBasePort;
  final String path;

  WebSocketService(
      {this.maxAttempts = 20,
      this.baseDelay = const Duration(seconds: 1),
      this.maxDelay = const Duration(seconds: 30),
      this.apiBasePort = 6789,
      this.path = '/ws'});

  String _buildUrl() {
    final host = Uri.base.host.isEmpty ? 'localhost' : Uri.base.host;
    final protocol = Uri.base.scheme == 'https' ? 'wss' : 'ws';
    return '$protocol://$host:$apiBasePort$path';
  }

  Future<void> connect() async {
    _disconnectInternal();
    _attempt = 0;
    _connectLoop(_buildUrl());
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
      notifyListeners();
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
        notifyListeners();
        _incoming.add({'type': 'ws_closed'});
        _scheduleReconnect(url);
      }, onError: (err) {
        _connected = false;
        notifyListeners();
        _incoming.add({'type': 'ws_error', 'error': err.toString()});
        _scheduleReconnect(url);
      });
    } catch (e) {
      _connected = false;
      notifyListeners();
      _incoming.add({'type': 'ws_error', 'error': e.toString()});
      _scheduleReconnect(url);
    }
  }

  void _scheduleReconnect(String url) {
    final attempt = _attempt;
    final backoffMs = (baseDelay.inMilliseconds * pow(2, max(0, attempt - 1)))
        .clamp(0, maxDelay.inMilliseconds);
    final jitter = Random().nextInt(500);
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

  Future<void> disconnect() async {
    _reconnectTimer?.cancel();
    _reconnectTimer = null;
    if (_channel != null) {
      try {
        _channel!.sink.close();
      } catch (_) {}
    }
    _disconnectInternal();
  }

  void _disconnectInternal() {
    _channel = null;
    _connected = false;
    notifyListeners();
  }

  @override
  void dispose() {
    disconnect();
    _incoming.close();
    super.dispose();
  }
}
