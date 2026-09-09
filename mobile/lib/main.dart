import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'screens/scanner_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const WarehouseERPApp());
}

class WarehouseERPApp extends StatelessWidget {
  const WarehouseERPApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Warehouse ERP Scanner',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blueGrey,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const AuthGate(),
    );
  }
}

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  static const _storage = FlutterSecureStorage();
  bool _isLoading = true;
  String? _token;
  String _baseUrl = '';

  @override
  void initState() {
    super.initState();
    _resolveDefaultBaseUrl();
    _checkStoredSession();
  }

  void _resolveDefaultBaseUrl() {
    if (kIsWeb) {
      _baseUrl = 'http://localhost:8000';
    } else if (Platform.isAndroid) {
      _baseUrl = 'http://10.0.2.2:8000'; // Standard Android Emulator host bridge
    } else {
      _baseUrl = 'http://127.0.0.1:8000'; // iOS Simulator & Desktop
    }
  }

  Future<void> _checkStoredSession() async {
    final token = await _storage.read(key: 'jwt_token');
    final storedUrl = await _storage.read(key: 'backend_url');

    setState(() {
      _token = token;
      if (storedUrl != null && storedUrl.isNotEmpty) {
        _baseUrl = storedUrl;
      }
      _isLoading = false;
    });
  }

  Future<void> _handleLogout() async {
    await _storage.delete(key: 'jwt_token');
    setState(() => _token = null);
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_token != null) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('Floor Operations'),
          actions: [
            IconButton(
              icon: const Icon(Icons.logout),
              tooltip: 'Log Out',
              onPressed: _handleLogout,
            ),
          ],
        ),
        body: WarehouseTransferScanner(
          authToken: _token!,
          backendBaseUrl: _baseUrl,
        ),
      );
    }

    return LoginScreen(
      initialBaseUrl: _baseUrl,
      onLoginSuccess: (token, resolvedUrl) {
        setState(() {
          _token = token;
          _baseUrl = resolvedUrl;
        });
      },
    );
  }
}

class LoginScreen extends StatefulWidget {
  final String initialBaseUrl;
  final void Function(String token, String resolvedUrl) onLoginSuccess;

  const LoginScreen({
    super.key,
    required this.initialBaseUrl,
    required this.onLoginSuccess,
  });

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _storage = const FlutterSecureStorage();
  final _dio = Dio();

  late final TextEditingController _urlController;
  final _userController = TextEditingController(text: 'floor_worker');
  final _passController = TextEditingController(text: 'FloorWorker123!');

  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: widget.initialBaseUrl);
  }

  @override
  void dispose() {
    _urlController.dispose();
    _userController.dispose();
    _passController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    final targetUrl = _urlController.text.trim();

    try {
      // FastAPI OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
      final response = await _dio.post(
        '$targetUrl/api/v1/auth/token',
        data: {
          'username': _userController.text.trim(),
          'password': _passController.text,
        },
        options: Options(
          contentType: Headers.formUrlEncodedContentType,
          receiveTimeout: const Duration(seconds: 10),
          sendTimeout: const Duration(seconds: 10),
        ),
      );

      final token = response.data['access_token'] as String;

      await _storage.write(key: 'jwt_token', value: token);
      await _storage.write(key: 'backend_url', value: targetUrl);

      widget.onLoginSuccess(token, targetUrl);
    } on DioException catch (e) {
      setState(() {
        _errorMessage = e.response?.data?['detail'] ?? 'Connection error: ${e.message}';
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'An unexpected error occurred.';
      });
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Icon(Icons.warehouse_rounded, size: 72, color: Colors.blueGrey),
                const SizedBox(height: 16),
                const Text(
                  'Warehouse ERP',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Sign in with operator credentials to initialize scanner',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey),
                ),
                const SizedBox(height: 32),
                TextField(
                  controller: _urlController,
                  decoration: const InputDecoration(
                    labelText: 'API Gateway URL',
                    prefixIcon: Icon(Icons.dns),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _userController,
                  decoration: const InputDecoration(
                    labelText: 'Username',
                    prefixIcon: Icon(Icons.person),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _passController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Password',
                    prefixIcon: Icon(Icons.lock),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 20),
                if (_errorMessage != null) ...[
                  Text(
                    _errorMessage!,
                    style: const TextStyle(color: Colors.redAccent, fontSize: 13),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 12),
                ],
                ElevatedButton(
                  onPressed: _isSubmitting ? null : _login,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: _isSubmitting
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Connect & Authenticate'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
