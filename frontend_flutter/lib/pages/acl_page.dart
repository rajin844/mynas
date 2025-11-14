// lib/pages/acl_page.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/acl_provider.dart';

class AclPage extends StatefulWidget {
  const AclPage({super.key});

  @override
  State<AclPage> createState() => _AclPageState();
}

class _AclPageState extends State<AclPage> {
  final pathCtrl = TextEditingController();

  @override
  Widget build(BuildContext context) {
    final acl = context.watch<AclProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('ACL')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(children: [
          Row(children: [
            Expanded(
                child: TextField(
                    controller: pathCtrl,
                    decoration: const InputDecoration(labelText: 'Path'))),
            ElevatedButton(
                onPressed: () => acl.loadAcl(pathCtrl.text.trim()),
                child: const Text('Load')),
          ]),
          const SizedBox(height: 12),
          Expanded(
              child: SingleChildScrollView(child: Text(acl.acl.toString()))),
        ]),
      ),
    );
  }
}
