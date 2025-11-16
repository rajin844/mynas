import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/acl_entry.dart';

class AclProvider extends ChangeNotifier {
  final ApiService api;
  List<AclEntry> acl = [];
  List<String> systemUsers = [];

  AclProvider({ApiService? api}) : api = api ?? ApiService();

  Future<void> loadUsers() async {
    final resp = await api.listUsers();
    systemUsers = resp.map<String>((e) => e["username"]).toList();
    notifyListeners();
  }

  Future<void> loadAcl(String path) async {
    final resp = await api.listAcl(path);
    acl = resp.map<AclEntry>((e) => AclEntry.fromJson(e)).toList();
    notifyListeners();
  }

  Future<void> setAclFull(String path, List<AclEntry> items) async {
    await api.setAcl(path, items.map((e) => e.toJson()).toList());
    await loadAcl(path);
  }

  Future<void> addEntry(String path, AclEntry entry) async {
    final newList = List<AclEntry>.from(acl)..add(entry);
    await setAclFull(path, newList);
  }

  Future<void> editEntry(String path, int index, AclEntry newEntry) async {
    final updatedList = List<AclEntry>.from(acl);
    updatedList[index] = newEntry;
    await setAclFull(path, updatedList);
  }

  Future<void> deleteEntry(String path, int index) async {
    final updatedList = List<AclEntry>.from(acl)..removeAt(index);
    await setAclFull(path, updatedList);
  }

  Future<void> removeAcl(String path) async {
    await api.removeAcl(path);
    acl.clear();
    notifyListeners();
  }
}
