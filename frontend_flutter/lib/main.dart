import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'services/api_service.dart';
import 'services/websocket_service.dart';

import 'providers/zfs_provider.dart';
import 'providers/shares_provider.dart';
import 'providers/monitoring_provider.dart';
import 'providers/backup_provider.dart';
import 'providers/network_provider.dart';
import 'providers/acl_provider.dart';
import 'providers/settings_provider.dart';

import 'pages/dashboard_page.dart';
import 'pages/pools_page.dart';
import 'pages/datasets_page.dart';
import 'pages/shares_page.dart';
import 'pages/acl_page.dart';
import 'pages/backup_page.dart';
import 'pages/network_page.dart';
import 'pages/monitoring_page.dart';
import 'pages/settings_page.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyNASApp());
}

class MyNASApp extends StatelessWidget {
  const MyNASApp({super.key});

  @override
  Widget build(BuildContext context) {
    final api = ApiService();
    final ws = WebSocketService(apiBasePort: 6789);
    ws.connect(); // start websocket in background

    return MultiProvider(
      providers: [
        Provider<ApiService>.value(value: api),
        ChangeNotifierProvider<WebSocketService>.value(value: ws),
        ChangeNotifierProvider(create: (_) => ZfsProvider(api: api)),
        ChangeNotifierProvider(create: (_) => SharesProvider(api: api)),
        ChangeNotifierProvider(create: (_) => MonitoringProvider(api: api)),
        ChangeNotifierProvider(create: (_) => BackupProvider(api: api)),
        ChangeNotifierProvider(create: (_) => NetworkProvider(api: api)),
        ChangeNotifierProvider(create: (_) => AclProvider(api: api)),
        ChangeNotifierProvider(create: (_) => SettingsProvider(api: api)),
      ],
      child: MaterialApp(
        title: 'MyNAS',
        theme: ThemeData.dark(useMaterial3: true),
        initialRoute: '/',
        routes: {
          '/': (ctx) => const DashboardPage(),
          '/pools': (ctx) => const PoolsPage(),
          '/datasets': (ctx) => const DatasetsPage(),
          '/shares': (ctx) => const SharesPage(),
          '/acl': (ctx) => const AclPage(),
          '/backup': (ctx) => const BackupPage(),
          '/network': (ctx) => const NetworkPage(),
          '/monitoring': (ctx) => const MonitoringPage(),
          '/settings': (ctx) => const SettingsPage(),
        },
      ),
    );
  }
}
