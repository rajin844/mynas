import 'package:flutter/material.dart';
import '../services/api_service.dart';

class NetworkProvider extends ChangeNotifier {
  final ApiService api;
  Map<String, dynamic> ifaces = {};

  NetworkProvider({ApiService? api}) : api = api ?? ApiService();

  Future<void> loadInterfaces() async {
    ifaces = await api.listInterfaces();
    notifyListeners();
  }
}
