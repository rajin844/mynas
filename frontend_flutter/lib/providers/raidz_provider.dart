import 'package:flutter/material.dart';
import '../services/api_service.dart';

class RaidzProvider extends ChangeNotifier {
  final ApiService api;

  List<Map<String, dynamic>> availableDisks = [];
  List<Map<String, dynamic>> selectedDisks = [];

  String layout = 'single';
  bool dryRun = true;
  Map<String, dynamic>? preview;
  String? lastResult;

  final TextEditingController poolNameController = TextEditingController();

  RaidzProvider({ApiService? api}) : api = api ?? ApiService();

  Future<void> loadAvailableDisks() async {
    try {
      final res = await api.listAvailableDisks();
      // expect list of maps
      availableDisks = List<Map<String, dynamic>>.from(res ?? []);
    } catch (e) {
      availableDisks = [];
    }
    notifyListeners();
  }

  void toggleDisk(Map<String, dynamic> d) {
    if (selectedDisks.contains(d)) {
      selectedDisks.remove(d);
    } else {
      selectedDisks.add(d);
    }
    notifyListeners();
  }

  void resetSelection() {
    selectedDisks = [];
    preview = null;
    notifyListeners();
  }

  void setLayout(String l) {
    layout = l;
    notifyListeners();
  }

  void setDryRun(bool v) {
    dryRun = v;
    notifyListeners();
  }

  Future<void> autoLayoutSuggested() async {
    // simple heuristic: for raidz1 need >=3, raidz2 >=4, raidz3 >=5
    if (selectedDisks.length < 2) {
      // try to auto add smallest or smallest two
      selectedDisks = availableDisks.take(2).toList();
    }
    if (selectedDisks.length >= 5) {
      layout = 'raidz2';
    } else if (selectedDisks.length >= 4) {
      layout = 'raidz1';
    } else if (selectedDisks.length == 3) {
      layout = 'mirror';
    } else {
      layout = 'single';
    }
    notifyListeners();
  }

  Future<void> previewLayout() async {
    final params = {
      'disks': selectedDisks,
      'layout': layout,
      'pool_name': poolNameController.text.trim(),
      'dry_run': true,
    };
    try {
      final res = await api.buildRaidzPreview(params);
      preview = Map<String, dynamic>.from(res ?? {});
    } catch (e) {
      preview = {'error': e.toString()};
    }
    notifyListeners();
  }

  bool get canCreate =>
      selectedDisks.isNotEmpty && poolNameController.text.trim().isNotEmpty;

  Future<void> createPool() async {
    final params = {
      'disks': selectedDisks,
      'layout': layout,
      'pool_name': poolNameController.text.trim(),
      'dry_run': dryRun,
    };
    try {
      final res = await api.createPoolFromRaidz(params);
      lastResult = res.toString();
      // optionally refresh global pools provider via other means
    } catch (e) {
      lastResult = 'Error: $e';
    }
    notifyListeners();
  }
}
