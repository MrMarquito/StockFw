import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class QueuedMovement {
  final String id;
  final String productId;
  final String sourceBinId;
  final String targetBinId;
  final int quantity;
  final String createdAt;

  QueuedMovement({
    required this.id,
    required this.productId,
    required this.sourceBinId,
    required this.targetBinId,
    required this.quantity,
    required this.createdAt,
  });

  Map<String, dynamic> toMap() => {
    'id': id,
    'product_id': productId,
    'source_bin_id': sourceBinId,
    'target_bin_id': targetBinId,
    'quantity': quantity,
    'created_at': createdAt,
  };
}

class LocalQueueDatabase {
  static final LocalQueueDatabase instance = LocalQueueDatabase._init();
  static Database? _database;

  LocalQueueDatabase._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('warehouse_queue.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE movement_queue (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            source_bin_id TEXT NOT NULL,
            target_bin_id TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            created_at TEXT NOT NULL
          )
        ''');
      },
    );
  }

  Future<void> enqueueTransfer(QueuedMovement movement) async {
    final db = await instance.database;
    await db.insert('movement_queue', movement.toMap());
  }

  Future<List<QueuedMovement>> getPendingTransfers() async {
    final db = await instance.database;
    final result = await db.query('movement_queue', orderBy: 'created_at ASC');
    return result.map((json) => QueuedMovement(
      id: json['id'] as String,
      productId: json['product_id'] as String,
      sourceBinId: json['source_bin_id'] as String,
      targetBinId: json['target_bin_id'] as String,
      quantity: json['quantity'] as int,
      createdAt: json['created_at'] as String,
    )).toList();
  }

  Future<void> removeTransfer(String id) async {
    final db = await instance.database;
    await db.delete('movement_queue', where: 'id = ?', whereArgs: [id]);
  }
}
