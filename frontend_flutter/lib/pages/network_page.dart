import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/network_provider.dart';

class NetworkPage extends StatefulWidget {
  const NetworkPage({super.key});

  @override
  State<NetworkPage> createState() => _NetworkPageState();
}

class _NetworkPageState extends State<NetworkPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      context.read<NetworkProvider>().loadInterfaces();
    });
  }

  @override
  Widget build(BuildContext context) {
    final np = context.watch<NetworkProvider>();
    final ifaces = np.interfaces;

    return Scaffold(
      appBar: AppBar(title: const Text("Network Interfaces")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: np.loading
            ? const Center(child: CircularProgressIndicator())
            : GridView.count(
                crossAxisCount: 2,
                childAspectRatio: 1.5,
                mainAxisSpacing: 16,
                crossAxisSpacing: 16,
                children: ifaces.entries.map((e) {
                  final name = e.key;
                  final iface = e.value;

                  final status = iface["status"] ?? "down";
                  final speed = iface["speed"] ?? "0 Mbps";
                  final ipv4 = iface["ipv4"] ?? "-";
                  final ipv6 = iface["ipv6"] ?? "-";
                  final dhcp = iface["dhcp"] == true;

                  return _buildInterfaceCard(
                      name, status, speed, ipv4, ipv6, dhcp);
                }).toList(),
              ),
      ),
    );
  }

  // -------------------------------------------------------------
  // STYLED CARD
  // -------------------------------------------------------------
  Widget _buildInterfaceCard(
    String name,
    String status,
    String speed,
    String ipv4,
    String ipv6,
    bool dhcp,
  ) {
    final isUp = status.toLowerCase() == "up";

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header Row
            Row(
              children: [
                Icon(
                  isUp ? Icons.network_ping : Icons.wifi_off,
                  color: isUp ? Colors.green : Colors.red,
                  size: 28,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    name.toUpperCase(),
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                    ),
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: dhcp ? Colors.blue[100] : Colors.orange[100],
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    dhcp ? "DHCP" : "STATIC",
                    style: const TextStyle(fontSize: 12),
                  ),
                )
              ],
            ),

            const SizedBox(height: 14),

            // SPEED
            Row(
              children: [
                const Icon(Icons.speed, size: 20, color: Colors.grey),
                const SizedBox(width: 8),
                Text(speed, style: const TextStyle(fontSize: 14)),
              ],
            ),

            const SizedBox(height: 10),

            // IPv4
            Row(
              children: [
                const Icon(Icons.language, size: 20, color: Colors.grey),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    "IPv4: $ipv4",
                    style: const TextStyle(fontSize: 13),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 6),

            // IPv6
            Row(
              children: [
                const Icon(Icons.language, size: 20, color: Colors.grey),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    "IPv6: $ipv6",
                    style: const TextStyle(fontSize: 13),
                  ),
                ),
              ],
            ),

            const Spacer(),

            // Settings Button
            Align(
              alignment: Alignment.bottomRight,
              child: TextButton.icon(
                icon: const Icon(Icons.settings),
                label: const Text("Configure"),
                onPressed: () {
                  _showNetworkConfig(name);
                },
              ),
            )
          ],
        ),
      ),
    );
  }

  // -------------------------------------------------------------
  // SETTINGS DIALOG (DHCP/Static)
  // -------------------------------------------------------------
  void _showNetworkConfig(String iface) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: Text("Configure $iface"),
        content: const Text("Static IP / DHCP editor coming soon."),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Close"))
        ],
      ),
    );
  }
}
