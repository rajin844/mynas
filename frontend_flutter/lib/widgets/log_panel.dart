import 'package:flutter/material.dart';

class LogPanel extends StatelessWidget {
  final List<String> logs;

  const LogPanel({super.key, required this.logs});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 150,
      color: Colors.black,
      child: ListView.builder(
        reverse: true,
        itemCount: logs.length,
        itemBuilder: (context,index){
          return Padding(
            padding: EdgeInsets.all(2),
            child: Text(logs[index], style: TextStyle(color: Colors.greenAccent, fontSize: 12)),
          );
        },
      ),
    );
  }
}
