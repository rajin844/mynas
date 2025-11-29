// lib/widgets/glass_card.dart
import 'dart:ui';
import 'package:flutter/material.dart';

class GlassCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color? titleColor;
  final Color? iconColor;
  final Widget child;
  final EdgeInsets padding;
  final List<Widget>? actions; // optional header actions (icons/buttons)

  const GlassCard({
    super.key,
    required this.title,
    required this.icon,
    required this.child,
    this.titleColor,
    this.iconColor,
    this.padding = const EdgeInsets.all(16),
    this.actions,
  });

  @override
  Widget build(BuildContext context) {
    final tc = titleColor ?? Colors.white;
    final ic = iconColor ?? Colors.white70;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.04)),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 6, sigmaY: 6),
          child: Container(
            color: const Color.fromRGBO(8, 12, 20, 0.56), // dark glass
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // header row
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.12),
                    borderRadius:
                        const BorderRadius.vertical(top: Radius.circular(14)),
                  ),
                  child: Row(
                    children: [
                      Icon(icon, color: ic, size: 18),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          title,
                          style: TextStyle(
                              color: tc,
                              fontWeight: FontWeight.w700,
                              fontSize: 15),
                        ),
                      ),
                      if (actions != null) ...[
                        Row(children: actions!),
                      ],
                    ],
                  ),
                ),

                // body
                Padding(
                  padding: padding,
                  child: child,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
