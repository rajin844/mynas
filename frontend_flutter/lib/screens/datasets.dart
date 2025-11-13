// lib/screens/datasets.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../provider/dataset_provider.dart';

class DatasetsScreen extends StatelessWidget {
  const DatasetsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final prov = Provider.of<DatasetProvider>(context);
    final TextEditingController ctr = TextEditingController();

    return Scaffold(
      appBar: AppBar(title: const Text('Datasets')),
      body: prov.loading
          ? Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Row(children: [
                    Expanded(
                        child: TextField(
                            controller: ctr,
                            decoration: InputDecoration(
                                labelText: 'New dataset name'))),
                    ElevatedButton(
                        onPressed: () async {
                          final name = ctr.text.trim();
                          if (name.isEmpty) return;
                          await prov.createDataset(name);
                          ctr.clear();
                        },
                        child: Text('Create'))
                  ]),
                ),
                Expanded(
                  child: ListView.builder(
                      itemCount: prov.datasets.length,
                      itemBuilder: (_, i) {
                        final d = prov.datasets[i];
                        final name = (d is Map && d.containsKey('name'))
                            ? d['name']
                            : d.toString();
                        return ListTile(
                          title: Text(name),
                          trailing: IconButton(
                            icon: Icon(Icons.delete, color: Colors.red),
                            onPressed: () async {
                              final ok = await showDialog<bool>(
                                context: context,
                                builder: (ctx) => AlertDialog(
                                  title: Text('Delete dataset'),
                                  content: Text('Delete dataset "$name"?'),
                                  actions: [
                                    TextButton(
                                        onPressed: () =>
                                            Navigator.pop(ctx, false),
                                        child: Text('Cancel')),
                                    TextButton(
                                        onPressed: () =>
                                            Navigator.pop(ctx, true),
                                        child: Text('Delete')),
                                  ],
                                ),
                              );
                              if (ok == true) await prov.deleteDataset(name);
                            },
                          ),
                        );
                      }),
                ),
              ],
            ),
    );
  }
}
