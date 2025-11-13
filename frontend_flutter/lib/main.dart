// lib/main.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/api_service.dart';
import 'services/websocket_service.dart';
import 'provider/dataset_provider.dart';
import 'screens/dashboard.dart';
import 'screens/pools.dart';
import 'screens/datasets.dart';
import 'screens/shares.dart';
import 'screens/acl.dart';
import 'screens/backup.dart';
import 'screens/network.dart';
import 'screens/monitoring.dart';
import 'widgets/drawer.dart';

void main() {
  runApp(MyNASApp());
}

class MyNASApp extends StatelessWidget {
  final api = ApiService(baseUrl: 'http://localhost:8000'); // change if needed
  final ws = WebSocketService();

  MyNASApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
            create: (_) => DatasetProvider(api: api, ws: ws)),
        // add other providers similarly when created
      ],
      child: MaterialApp(
        title: 'MyNAS',
        theme: ThemeData(primarySwatch: Colors.blue),
        initialRoute: '/',
        routes: {
          '/': (_) => HomeShell(api: api, ws: ws),
          '/pools': (_) => PoolsScreen(),
          '/datasets': (_) => DatasetsScreen(),
          '/shares': (_) => SharesScreen(),
          '/acl': (_) => AclScreen(),
          '/backup': (_) => BackupScreen(),
          '/network': (_) => NetworkScreen(),
          '/monitoring': (_) => MonitoringScreen(),
        },
      ),
    );
  }
}

class HomeShell extends StatefulWidget {
  final ApiService api;
  final WebSocketService ws;
  const HomeShell({super.key, required this.api, required this.ws});
  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  @override
  void initState() {
    super.initState();
    widget.ws.event = (evt) {
      // broadcast to providers if needed; simple example:
      if (evt['event'] == 'dataset_created' ||
          evt['event'] == 'dataset_deleted') {
        Provider.of<DatasetProvider>(context, listen: false).fetchDatasets();
      }
    };
    widget.ws.connect('ws://127.0.0.1:8000/ws');
  }

  @override
  void dispose() {
    widget.ws.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('MyNAS Dashboard')),
      drawer: AppDrawer(onSelect: (route) {
        Navigator.of(context).pushNamed(route);
      }),
      body: DashboardScreen(api: widget.api),
    );
  }
}
