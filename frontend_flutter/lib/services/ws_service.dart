import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketService {
  final channel = WebSocketChannel.connect(Uri.parse('ws://127.0.0.1:8000/ws'));
  Stream<dynamic> get stream => channel.stream.map((m) => jsonDecode(m));
}
