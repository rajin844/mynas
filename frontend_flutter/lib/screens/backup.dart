// lib/screens/backup.dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class BackupScreen extends StatefulWidget {
  const BackupScreen({super.key});

  @override
  State<BackupScreen> createState() => _BackupScreenState();
}

class _BackupScreenState extends State<BackupScreen> {
  final api = ApiService(baseUrl: 'http://localhost:8000');
  List backups = [];

  @override
  void initState() {
    super.initState();
    fetchBackups();
  }

  Future<void> fetchBackups() async {
    try {
      final res = await api.callRpc('backup', 'list', {});
      if (res is Map && res.containsKey('backups')) {
        backups = List.from(res['backups']);
      }
      setState(() {});
    } catch (e, st) {
      debugPrint('Backup error: $e\n$st'); // or use logger}
    }
  }

  Future<void> createBackup() async {
    await api.callRpc('backup', 'create', {});
    await fetchBackups();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: AppBar(title: Text('Backups')),
        body: Column(children: [
          ElevatedButton(onPressed: createBackup, child: Text('Create Backup')),
          Expanded(
              child: ListView.builder(
                  itemCount: backups.length,
                  itemBuilder: (_, i) => ListTile(title: Text(backups[i]))))
        ]));
  }
}
