// lib/services/websocket_service.dart
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:async';
import 'package:flutter/material.dart';

class WebSocketService with ChangeNotifier {
  WebSocketChannel? _channel;
  String? baseurl;
  

  StreamSubscription? _streamSubscription;
  bool _isConnected = false;

  ValueChanged<Map<String, dynamic>>? event;

  bool get isConnected => _isConnected;

  Future<void> connect(String url) async {
    // Note: 'baseurl' variable needs to be defined as a field in your class
    // baseurl = url;
    try {
      _channel = WebSocketChannel.connect(Uri.parse(url));
      _isConnected = true;
      notifyListeners();

      _streamSubscription = _channel!.stream.listen(
        (message) {
          // Assuming messages are JSON strings
          try {
            final decodedMessage = jsonDecode(message);
            // Quick fix to satisfy the linter/analyzer
            debugPrint('Received message: $decodedMessage');
            // If 'event' callback is set, call it
            if (decodedMessage is Map<String, dynamic> && event != null) {
              event!(decodedMessage);
            }
          } catch (e) {
            debugPrint("Error decoding message: $e");
          }
        },
        onDone: () {
          _isConnected = false;
          notifyListeners();
          debugPrint("WebSocket disconnected. Attempting to reconnect...");
          // Optional: implement reconnection logic here
        },
        onError: (error) {
          _isConnected = false;
          notifyListeners();
          debugPrint("WebSocket error: $error");
        },
      );
    } catch (e) {
      debugPrint("Could not connect to WebSocket: $e");
      _isConnected = false;
      notifyListeners();
    }
  }

  void disconnect() {
    _streamSubscription?.cancel();
    _channel?.sink.close();
    _isConnected = false;
    notifyListeners();
  }

  /// Set event/message listener
  void setListener(Function(Map<String, dynamic>) listener) {
    // ✅ Fix #2 here
    event = listener;
  }

  void send(Map<String, dynamic> data) {
    if (_isConnected && _channel != null) {
      final messageString = jsonEncode(data);
      _channel!.sink.add(messageString);
    } else {
      debugPrint("WebSocket not connected, cannot send message.");
    }
  }

  // Expose the stream for providers or widgets to listen to
  Stream? get stream => _channel?.stream;
}
