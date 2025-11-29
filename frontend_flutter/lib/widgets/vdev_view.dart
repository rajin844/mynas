// lib/widgets/vdev_view.dart
import 'package:flutter/material.dart';

class VdevView extends StatelessWidget {
  final List<dynamic> vdevs;
  const VdevView({super.key, required this.vdevs});

  @override
  Widget build(BuildContext context) {
    return Column(
        children: vdevs.map((v) {
      return Card(
          child: ListTile(
        title: Text("${v['type']}"),
        subtitle: Text(
            "Devices: ${(v['devices'] as List).join(', ')}\nUsable: ${v['usable_bytes'] ?? 'N/A'}"),
      ));
    }).toList());
  }
}
