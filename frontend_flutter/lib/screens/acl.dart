// lib/screens/acl.dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AclScreen extends StatefulWidget {
  const AclScreen({super.key});

  @override
  State<AclScreen> createState() => _AclScreenState();
}

class _AclScreenState extends State<AclScreen> {
  final api = ApiService(baseUrl: 'http://localhost:8000');
  List acls = [];

  @override
  void initState() {
    super.initState();
    fetchAcls();
  }

  Future<void> fetchAcls() async {
    try {
      final res = await api.callRpc('ACL', 'list', {});
      if (res is List) acls = res;
      setState(() {});
    } catch (e, st) {
      debugPrint('ACL error: $e\n$st');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: AppBar(title: Text('ACL')),
        body: ListView.builder(
          itemCount: acls.length,
          itemBuilder: (_, i) {
            final a = acls[i];
            return ListTile(title: Text(a.toString()));
          },
        ));
  }
}
