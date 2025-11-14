// lib/pages/settings_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/settings_provider.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});
  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => context.read<SettingsProvider>().load());
  }

  @override
  Widget build(BuildContext context) {
    final sp = context.watch<SettingsProvider>();
    return Scaffold(
      appBar: AppBar(title: const Text('System Settings')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: ListView(children: [
          Text('Settings: ${sp.settings}'),
        ]),
      ),
    );
  }
}
