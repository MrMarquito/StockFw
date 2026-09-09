import 'package:flutter/material.dart';

void main() {
  runApp(const WarehouseScannerApp());
}

class WarehouseScannerApp extends StatelessWidget {
  const WarehouseScannerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'StockFW Scanner OS',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF090D16),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00E676),      // Tactical Cyber Emerald
          secondary: Color(0xFFFFAB00),    // Warning Amber
          surface: Color(0xFF131A29),      // Deep Steel Container
          background: Color(0xFF090D16),
          error: Color(0xFFFF3D71),
        ),
        fontFamily: 'monospace',
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: const Color(0xFF161F33),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: Color(0xFF22314E)),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: Color(0xFF00E676), width: 2),
          ),
          labelStyle: const TextStyle(color: Color(0xFF7E8B9B), fontSize: 13),
        ),
      ),
      home: const IndustrialDashboard(),
    );
  }
}

class IndustrialDashboard extends StatefulWidget {
  const IndustrialDashboard({super.key});

  @override
  State<IndustrialDashboard> createState() => _IndustrialDashboardState();
}

class _IndustrialDashboardState extends State<IndustrialDashboard> {
  int _currentStep = 0;
  String _sourceBin = "BIN-A-01-A";
  String _product = "SKU-BRG-100";
  String _targetBin = "BIN-B-02-B";
  int _quantity = 25;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF0F1523),
        elevation: 0,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF00E676).withOpacity(0.15),
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: const Color(0xFF00E676), width: 1),
              ),
              child: const Text(
                "SYS::ONLINE",
                style: TextStyle(color: Color(0xFF00E676), fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(width: 12),
            const Text(
              "STOCK-FW // SCANNER",
              style: TextStyle(fontSize: 16, letterSpacing: 1.5, fontWeight: FontWeight.w900),
            ),
          ],
        ),
      ),
      body: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 520),
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 🔲 Tactical HUD Viewport
              Container(
                height: 220,
                decoration: BoxDecoration(
                  color: const Color(0xFF0C111C),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF1E293B)),
                ),
                child: Stack(
                  children: [
                    // Corner accents
                    Positioned(top: 12, left: 12, child: _hudCorner()),
                    Positioned(top: 12, right: 12, child: Transform.flip(flipX: true, child: _hudCorner())),
                    Positioned(bottom: 12, left: 12, child: Transform.flip(flipY: true, child: _hudCorner())),
                    Positioned(bottom: 12, right: 12, child: Transform.flip(flipX: true, flipY: true, child: _hudCorner())),

                    // Reticle Center
                    Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.qr_code_scanner, size: 56, color: Color(0xFF00E676)),
                          const SizedBox(height: 12),
                          Text(
                            "CURRENT TARGET: ${_stepLabel(_currentStep)}",
                            style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8), letterSpacing: 1.2),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // 📊 Operational Status Card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF131A29),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF22314E)),
                ),
                child: Column(
                  children: [
                    _telemetryRow("SOURCE", _sourceBin, Icons.upload),
                    const Divider(color: Color(0xFF1E293B), height: 16),
                    _telemetryRow("ITEM SKU", _product, Icons.inventory_2),
                    const Divider(color: Color(0xFF1E293B), height: 16),
                    _telemetryRow("DESTINATION", _targetBin, Icons.download),
                    const Divider(color: Color(0xFF1E293B), height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text("QUANTITY", style: TextStyle(fontSize: 12, color: Color(0xFF64748B))),
                        Row(
                          children: [
                            IconButton(
                              onPressed: () => setState(() => _quantity = (_quantity > 1) ? _quantity - 1 : 1),
                              icon: const Icon(Icons.remove, size: 16),
                            ),
                            Text("$_quantity UNITS", style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFFFFAB00))),
                            IconButton(
                              onPressed: () => setState(() => _quantity++),
                              icon: const Icon(Icons.add, size: 16),
                            ),
                          ],
                        )
                      ],
                    ),
                  ],
                ),
              ),
              const Spacer(),

              // ⚡ Execution Trigger Button
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00E676),
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      backgroundColor: const Color(0xFF00E676),
                      content: Text(
                        "DISPATCH RECORDED: Transfer of $_quantity units committed.",
                        style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.bolt, color: Colors.black),
                label: const Text(
                  "EXECUTE TRANSACTION",
                  style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1.2),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _telemetryRow(String label, String value, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 16, color: const Color(0xFF00E676)),
        const SizedBox(width: 8),
        Text(label, style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
        const Spacer(),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
      ],
    );
  }

  Widget _hudCorner() {
    return Container(
      width: 14,
      height: 14,
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(color: Color(0xFF00E676), width: 2),
          left: BorderSide(color: Color(0xFF00E676), width: 2),
        ),
      ),
    );
  }

  String _stepLabel(int step) {
    switch (step) {
      case 0: return "SOURCE BIN LOCATION";
      case 1: return "PRODUCT BARCODE / SKU";
      case 2: return "TARGET BIN DESTINATION";
      default: return "TRANSFER CONFIRMATION";
    }
  }
}
