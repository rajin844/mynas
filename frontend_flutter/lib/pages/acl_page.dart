import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/acl_provider.dart';
import '../models/acl_entry.dart';

class AclPage extends StatefulWidget {
  const AclPage({super.key});

  @override
  State<AclPage> createState() => _AclPageState();
}

class _AclPageState extends State<AclPage> {
  final pathCtrl = TextEditingController();
  final userSearchCtrl = TextEditingController();

  bool read = true;
  bool write = false;
  bool exec = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      context.read<AclProvider>().loadUsers();
    });
  }

  String permissionsString() {
    return "${read ? 'r' : ''}${write ? 'w' : ''}${exec ? 'x' : ''}";
  }

  void loadPreset(String preset) {
    setState(() {
      switch (preset) {
        case "Read-Only":
          read = true;
          write = false;
          exec = false;
          break;
        case "Read-Write":
          read = true;
          write = true;
          exec = false;
          break;
        case "Full Access":
          read = true;
          write = true;
          exec = true;
          break;
        case "No Access":
          read = false;
          write = false;
          exec = false;
          break;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AclProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text("ACL Manager"), centerTitle: true),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => provider.loadAcl(pathCtrl.text.trim()),
        label: const Text("Reload ACL"),
        icon: const Icon(Icons.refresh),
      ),
      body: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          children: [
            // PATH INPUT
            TextField(
              controller: pathCtrl,
              decoration: const InputDecoration(
                labelText: "Path",
                prefixIcon: Icon(Icons.folder),
              ),
            ),

            const SizedBox(height: 20),

            // SEARCHABLE USER FIELD
            TextField(
              controller: userSearchCtrl,
              decoration: const InputDecoration(
                labelText: "Search User",
                prefixIcon: Icon(Icons.search),
              ),
              onChanged: (v) => setState(() {}),
            ),

            const SizedBox(height: 10),

            SizedBox(
              height: 120,
              child: ListView(
                children: provider.systemUsers
                    .where((u) => u.contains(userSearchCtrl.text))
                    .map((u) => ListTile(
                          leading: const Icon(Icons.person),
                          title: Text(u),
                          onTap: () {
                            userSearchCtrl.text = u;
                          },
                        ))
                    .toList(),
              ),
            ),

            const SizedBox(height: 20),

            // PERMISSION CHIPS
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                FilterChip(
                    label: const Text("R"),
                    selected: read,
                    onSelected: (v) => setState(() => read = v)),
                FilterChip(
                    label: const Text("W"),
                    selected: write,
                    onSelected: (v) => setState(() => write = v)),
                FilterChip(
                    label: const Text("X"),
                    selected: exec,
                    onSelected: (v) => setState(() => exec = v)),
              ],
            ),

            const SizedBox(height: 20),

            // PRESETS
            Wrap(
              spacing: 10,
              children: [
                ElevatedButton(
                    onPressed: () => loadPreset("Read-Only"),
                    child: const Text("Read-Only")),
                ElevatedButton(
                    onPressed: () => loadPreset("Read-Write"),
                    child: const Text("Read-Write")),
                ElevatedButton(
                    onPressed: () => loadPreset("Full Access"),
                    child: const Text("Full Access")),
                OutlinedButton(
                    onPressed: () => loadPreset("No Access"),
                    child: const Text("Clear")),
              ],
            ),

            const SizedBox(height: 20),

            ElevatedButton.icon(
              onPressed: () {
                final entry = AclEntry(
                  username: userSearchCtrl.text,
                  permissions: permissionsString(),
                );
                provider.addEntry(pathCtrl.text.trim(), entry);
              },
              icon: const Icon(Icons.add),
              label: const Text("Add Entry"),
            ),

            const SizedBox(height: 20),

            Expanded(
              child: provider.acl.isEmpty
                  ? const Center(child: Text("No ACL entries"))
                  : ListView.builder(
                      itemCount: provider.acl.length,
                      itemBuilder: (context, i) {
                        final entry = provider.acl[i];

                        return Card(
                          child: ListTile(
                            leading: const Icon(Icons.security),
                            title: Text(entry.username),
                            subtitle: Text("Permissions: ${entry.permissions}"),
                            trailing: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                // EDIT BUTTON
                                IconButton(
                                  icon: const Icon(Icons.edit),
                                  onPressed: () {
                                    // load values into edit state
                                    userSearchCtrl.text = entry.username;
                                    read = entry.permissions.contains('r');
                                    write = entry.permissions.contains('w');
                                    exec = entry.permissions.contains('x');

                                    provider.editEntry(
                                      pathCtrl.text.trim(),
                                      i,
                                      AclEntry(
                                          username: entry.username,
                                          permissions: permissionsString()),
                                    );
                                  },
                                ),

                                // DELETE BUTTON
                                IconButton(
                                  icon: const Icon(Icons.delete,
                                      color: Colors.red),
                                  onPressed: () {
                                    provider.deleteEntry(
                                        pathCtrl.text.trim(), i);
                                  },
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),

            ElevatedButton(
              onPressed: () => provider.removeAcl(pathCtrl.text.trim()),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
              child: const Text("Delete ALL ACL"),
            )
          ],
        ),
      ),
    );
  }
}
