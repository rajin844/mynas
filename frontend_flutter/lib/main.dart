import 'package:flutter/material.dart';
import 'package:frontend_flutter/providers/dataset_provider.dart';
import 'package:frontend_flutter/providers/raidz_provider.dart';
import 'package:frontend_flutter/providers/smart_provider.dart';
import 'package:frontend_flutter/providers/storage_provider.dart';
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
import 'pages/storage_page.dart';
import 'pages/pools_page.dart';
import 'pages/datasets_page.dart';
import 'pages/shares_page.dart';
import 'pages/acl_page.dart';
import 'pages/backup_page.dart';
import 'pages/network_page.dart';
import 'pages/monitoring_page.dart';
import 'pages/settings_page.dart';
//import 'pages/zfs_manager_page.dart';
//import 'pages/raidz_builder_page.dart';
//import 'pages/snapshots_page.dart';
//import 'pages/users_page.dart';
//2import 'pages/tasks_page.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyNASApp());
}

class MyNASApp extends StatelessWidget {
  const MyNASApp({super.key});

  @override
  Widget build(BuildContext context) {
    final api = ApiService();
    final ws = WebSocketService(wsPort: 6789);
    ws.connect(); // start websocket in background

    return MultiProvider(
      providers: [
        Provider<ApiService>.value(value: api),
        ChangeNotifierProvider<WebSocketService>.value(value: ws),

        //Provider(create: (_) => ApiService()),

        //ChangeNotifierProvider(create: (_) => WebSocketService()),
        ChangeNotifierProvider(
            create: (c) => MonitoringProvider(api: c.read<ApiService>())),

        ChangeNotifierProvider(
            create: (c) => StorageProvider(
                api: c.read<ApiService>(), ws: c.read<WebSocketService>())),

        ChangeNotifierProvider(
            create: (c) => RaidzProvider(
                api: c.read<ApiService>(), ws: c.read<WebSocketService>())),

        ChangeNotifierProvider(
            create: (c) => SmartProvider(
                api: c.read<ApiService>(), ws: c.read<WebSocketService>())),

        ChangeNotifierProvider(
            create: (c) => DatasetProvider(
                api: c.read<ApiService>(), ws: c.read<WebSocketService>())),

        ChangeNotifierProvider(
            create: (c) => ZfsProvider(
                api: c.read<ApiService>(), ws: c.read<WebSocketService>())),

        ChangeNotifierProvider(
            create: (c) => SharesProvider(api: c.read<ApiService>())),

        ChangeNotifierProvider(
            create: (c) => AclProvider(api: c.read<ApiService>())),

        // ChangeNotifierProvider(create: (_) => StorageProvider(api: api, ws: ws)),
        //ChangeNotifierProvider(create: (_) => SharesProvider(api: api)),
        // ChangeNotifierProvider(create: (_) => MonitoringProvider(api: api)),
        ChangeNotifierProvider(create: (_) => BackupProvider(api: api, ws: ws)),
        ChangeNotifierProvider(
            create: (_) => NetworkProvider(api: api, ws: ws)),
        //ChangeNotifierProvider(create: (_) => AclProvider(api: api)),
        ChangeNotifierProvider(create: (_) => SettingsProvider(api: api)),
      ],
      child: MaterialApp(
          title: 'MyNAS',
          debugShowCheckedModeBanner: false,
          theme: ThemeData(
            useMaterial3: true,
            colorSchemeSeed: Colors.blueAccent,
            brightness: Brightness.dark,

            // ---- PRIMARY FONT ----
            fontFamily: 'Roboto', // Google CDN (HTML Renderer)

            // ---- FALLBACKS (LOCAL) ----
            fontFamilyFallback: [
              'RobotoLocal',
              'NotoSansLocal',
              'NotoSymbolsLocal',
              'MaterialIconsLocal',
            ],

            iconTheme: const IconThemeData(size: 22),
            visualDensity: VisualDensity.adaptivePlatformDensity,
          ),
          darkTheme: ThemeData(
            useMaterial3: true,
            brightness: Brightness.light,
            colorSchemeSeed: Colors.blueGrey,

            // --- Primary font ---
            fontFamily: 'Roboto',

            // --- Local fallback fonts ---
            fontFamilyFallback: [
              'RobotoLocal',
              'NotoSansLocal',
              'NotoSymbolsLocal',
              'MaterialIconsLocal',
            ],
          ),
          // Auto-switch based on system theme
          //themeMode: ThemeMode.system,
          themeMode: ThemeMode.system,
          initialRoute: '/',
          routes: {
            "/": (ctx) => const DashboardPage(),
            "/storage": (context) => const StoragePage(),
            "/pools": (ctx) => const PoolsPage(),
            "/datasets": (ctx) => const DatasetsPage(),
            "/shares": (ctx) => const SharesPage(),
            "/acl": (ctx) => const AclPage(),
            "/backup": (ctx) => const BackupPage(),
            "/network": (ctx) => const NetworkPage(),
            "/monitoring": (ctx) => const MonitoringPage(),
            //"/raidz": (ctx) => const RaidzBuilderPage(),
            //"/snapshots": (ctx) => const SnapshotsPage(),
            //"/users": (ctx) => const UsersPage(),
            //"/tasks": (ctx) => const TasksPage(),
            "/settings": (ctx) => const SettingsPage(),
            // ⚠ These must be added or removed from the drawer
            "/alerts": (_) =>
                Scaffold(body: Center(child: Text("Alerts Screen"))),
            "/maint": (_) =>
                Scaffold(body: Center(child: Text("Maintenance Tools"))),
          }),
    );
  }
}
