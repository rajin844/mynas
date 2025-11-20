import 'package:flutter/material.dart';

class MetricCard extends StatelessWidget {
  final String label; // CPU, RAM, Disk
  final double value; // numeric %

  const MetricCard({required this.label, required this.value, super.key});

  IconData _getIcon() {
    switch (label.toLowerCase()) {
      case "cpu":
        return Icons.speed; // Best CPU icon
      case "ram":
        return Icons.memory; // RAM icon
      case "disk":
        return Icons.storage; // HDD / Disk icon
      default:
        return Icons.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Icon at top
            Icon(
              _getIcon(),
              size: 36,
              color: Theme.of(context).colorScheme.primary,
            ),

            const SizedBox(height: 12),

            // CPU / RAM / Disk label
            Text(
              label,
              style: Theme.of(context).textTheme.titleMedium,
            ),

            const SizedBox(height: 12),

            // Percentage value
            Text(
              "${value.toStringAsFixed(1)}%",
              style: const TextStyle(
                fontSize: 26,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 12),

            // Progress bar
            LinearProgressIndicator(
              value: value / 100,
              borderRadius: BorderRadius.circular(10),
              minHeight: 8,
            )
          ],
        ),
      ),
    );
  }
}
