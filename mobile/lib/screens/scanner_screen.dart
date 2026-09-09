import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:dio/dio.dart';

enum ScanStep { scanSourceBin, scanProduct, scanTargetBin, complete }

class WarehouseTransferScanner extends StatefulWidget {
  final String authToken;
  final String backendBaseUrl;

  const WarehouseTransferScanner({
    super.key,
    required this.authToken,
    required this.backendBaseUrl,
  });

  @override
  State<WarehouseTransferScanner> createState() => _WarehouseTransferScannerState();
}

class _WarehouseTransferScannerState extends State<WarehouseTransferScanner> {
  ScanStep _currentStep = ScanStep.scanSourceBin;
  String? _sourceBinId;
  String? _productId;
  String? _targetBinId;
  int _quantity = 1;
  bool _isProcessing = false;

  final Dio _dio = Dio();
  final TextEditingController _manualInputController = TextEditingController();

  void _processCode(String rawCode) {
    setState(() {
      if (_currentStep == ScanStep.scanSourceBin) {
        _sourceBinId = rawCode;
        _currentStep = ScanStep.scanProduct;
      } else if (_currentStep == ScanStep.scanProduct) {
        _productId = rawCode;
        _currentStep = ScanStep.scanTargetBin;
      } else if (_currentStep == ScanStep.scanTargetBin) {
        _targetBinId = rawCode;
        _currentStep = ScanStep.complete;
      }
    });
  }

  void _onDetect(BarcodeCapture capture) {
    if (_isProcessing) return;
    final barcode = capture.barcodes.firstOrNull?.rawValue;
    if (barcode == null) return;

    setState(() => _isProcessing = true);
    _processCode(barcode);

    Future.delayed(const Duration(milliseconds: 750), () {
      if (mounted) setState(() => _isProcessing = false);
    });
  }

  void _showManualInputDialog() {
    _manualInputController.clear();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Enter ${_currentStep.name} UUID'),
        content: TextField(
          controller: _manualInputController,
          autofocus: true,
          decoration: const InputDecoration(
            hintText: 'e.g. 550e8400-e29b-41d4-a716-446655440000',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              final text = _manualInputController.text.trim();
              if (text.isNotEmpty) {
                _processCode(text);
                Navigator.pop(context);
              }
            },
            child: const Text('Apply'),
          ),
        ],
      ),
    );
  }

  Future<void> _submitTransfer() async {
    final payload = {
      "product_id": _productId,
      "source_bin_id": _sourceBinId,
      "target_bin_id": _targetBinId,
      "quantity": _quantity,
    };

    try {
      final response = await _dio.post(
        '${widget.backendBaseUrl}/api/v1/inventory/transfer',
        data: payload,
        options: Options(headers: {"Authorization": "Bearer ${widget.authToken}"}),
      );

      if (response.statusCode == 200 && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Stock Transfer Executed Successfully')),
        );
        _resetFlow();
      }
    } on DioException catch (e) {
      if (mounted) {
        final errorMsg = e.response?.data?['detail'] ?? 'Transfer execution failed';
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(errorMsg)));
      }
    }
  }

  void _resetFlow() {
    setState(() {
      _currentStep = ScanStep.scanSourceBin;
      _sourceBinId = null;
      _productId = null;
      _targetBinId = null;
      _quantity = 1;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          // Left: Camera viewport (or fallback preview on web)
          Expanded(
            flex: 3,
            child: Stack(
              children: [
                MobileScanner(onDetect: _onDetect),
                Positioned(
                  bottom: 16,
                  left: 16,
                  child: ElevatedButton.icon(
                    onPressed: _currentStep == ScanStep.complete ? null : _showManualInputDialog,
                    icon: const Icon(Icons.keyboard),
                    label: const Text('Manual UUID Input'),
                  ),
                ),
              ],
            ),
          ),
          // Right: Status inspector & step controller
          Expanded(
            flex: 2,
            child: Container(
              color: Theme.of(context).colorScheme.surface,
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Step: ${_currentStep.name.toUpperCase()}',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                  ),
                  const Divider(height: 32),
                  ListTile(
                    dense: true,
                    title: const Text('Source Bin'),
                    subtitle: Text(_sourceBinId ?? 'Pending...'),
                    leading: Icon(
                      Icons.check_circle,
                      color: _sourceBinId != null ? Colors.green : Colors.grey,
                    ),
                  ),
                  ListTile(
                    dense: true,
                    title: const Text('Product SKU ID'),
                    subtitle: Text(_productId ?? 'Pending...'),
                    leading: Icon(
                      Icons.check_circle,
                      color: _productId != null ? Colors.green : Colors.grey,
                    ),
                  ),
                  ListTile(
                    dense: true,
                    title: const Text('Target Bin'),
                    subtitle: Text(_targetBinId ?? 'Pending...'),
                    leading: Icon(
                      Icons.check_circle,
                      color: _targetBinId != null ? Colors.green : Colors.grey,
                    ),
                  ),
                  const Spacer(),
                  if (_currentStep == ScanStep.complete) ...[
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Transfer Units:'),
                        Row(
                          children: [
                            IconButton(
                              icon: const Icon(Icons.remove),
                              onPressed: () => setState(() => _quantity = (_quantity > 1) ? _quantity - 1 : 1),
                            ),
                            Text('$_quantity', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                            IconButton(
                              icon: const Icon(Icons.add),
                              onPressed: () => setState(() => _quantity++),
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
                        onPressed: _submitTransfer,
                        child: const Text('Execute Transfer'),
                      ),
                    ),
                  ],
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton(
                      onPressed: _resetFlow,
                      child: const Text('Reset Scanner Flow'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
