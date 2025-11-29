import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/zfs_provider.dart';

// Grid of datasets
class DatasetOverviewGrid extends StatelessWidget {
  final List<dynamic> datasets;
  const DatasetOverviewGrid({super.key, required this.datasets});

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      childAspectRatio: 3,
      children: datasets.map((ds) {
        return Card(
          child: ListTile(
            title: Text(ds["name"], overflow: TextOverflow.ellipsis),
            subtitle: Text("Used: ${ds["used"]} • Avail: ${ds["avail"]}"),
          ),
        );
      }).toList(),
    );
  }
}
