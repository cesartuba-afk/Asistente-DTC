import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';
import 'package:provider/provider.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => BluetoothScanner()),
        ChangeNotifierProvider(create: (_) => ObdSession()),
      ],
      child: const Elm327App(),
    ),
  );
}

class Elm327App extends StatelessWidget {
  const Elm327App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ELM327 Scanner',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueGrey),
        useMaterial3: true,
      ),
      home: const BluetoothScannerPage(),
    );
  }
}

class BluetoothScannerPage extends StatelessWidget {
  const BluetoothScannerPage({super.key});

  @override
  Widget build(BuildContext context) {
    final scanner = context.watch<BluetoothScanner>();
    final session = context.watch<ObdSession>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Escáner ELM327 v1.5'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: scanner.isScanning ? null : scanner.startDiscovery,
          ),
        ],
      ),
      body: Column(
        children: [
          if (scanner.error != null)
            MaterialBanner(
              content: Text(scanner.error!),
              backgroundColor: Theme.of(context).colorScheme.errorContainer,
              actions: [
                TextButton(
                  onPressed: () => scanner.clearError(),
                  child: const Text('Cerrar'),
                ),
              ],
            ),
          SwitchListTile.adaptive(
            title: const Text('Bluetooth'),
            value: scanner.isBluetoothEnabled,
            onChanged: (value) => value
                ? scanner.enableBluetooth()
                : scanner.disableBluetooth(),
          ),
          Expanded(
            child: RefreshIndicator(
              onRefresh: scanner.startDiscovery,
              child: ListView.builder(
                itemCount: scanner.devices.length,
                itemBuilder: (context, index) {
                  final result = scanner.devices[index];
                  final device = result.device;
                  final isConnected =
                      session.connectedDevice?.address == device.address;
                  return ListTile(
                    title:
                        Text(device.name ?? 'Dispositivo sin nombre'),
                    subtitle:
                        Text(device.address ?? 'Dirección desconocida'),
                    trailing: isConnected
                        ? const Icon(Icons.check_circle, color: Colors.green)
                        : null,
                    onTap: () async {
                      if (isConnected) {
                        await session.disconnect();
                      } else {
                        await session.connect(result);
                      }
                    },
                  );
                },
              ),
            ),
          ),
          const Divider(height: 1),
          _ObdStatusCard(session: session),
        ],
      ),
    );
  }
}

class _ObdStatusCard extends StatelessWidget {
  const _ObdStatusCard({required this.session});

  final ObdSession session;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      width: double.infinity,
      color: Theme.of(context).colorScheme.surfaceVariant,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'Estado de conexión',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Text(session.statusMessage),
          const SizedBox(height: 16),
          if (session.isConnected)
            Wrap(
              spacing: 8,
              children: [
                ElevatedButton.icon(
                  onPressed: session.fetchVehicleInfo,
                  icon: const Icon(Icons.directions_car),
                  label: const Text('Info vehículo'),
                ),
                ElevatedButton.icon(
                  onPressed: session.fetchTroubleCodes,
                  icon: const Icon(Icons.warning),
                  label: const Text('Leer DTCs'),
                ),
                ElevatedButton.icon(
                  onPressed: session.clearTroubleCodes,
                  icon: const Icon(Icons.cleaning_services),
                  label: const Text('Borrar DTCs'),
                ),
              ],
            ),
          if (session.messages.isNotEmpty)
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Divider(height: 24),
                Text('Mensajes del OBD-II',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                ...session.messages
                    .map((message) => Text('• $message'))
                    .toList(),
              ],
            ),
        ],
      ),
    );
  }
}

class BluetoothScanner extends ChangeNotifier {
  BluetoothScanner() {
    _init();
  }

  final List<BluetoothDiscoveryResult> _devices = [];
  bool _isScanning = false;
  bool _isBluetoothEnabled = false;
  String? _error;

  List<BluetoothDiscoveryResult> get devices => List.unmodifiable(_devices);
  bool get isScanning => _isScanning;
  bool get isBluetoothEnabled => _isBluetoothEnabled;
  String? get error => _error;

  Future<void> _init() async {
    final state = await FlutterBluetoothSerial.instance.state;
    _isBluetoothEnabled = state == BluetoothState.STATE_ON;
    notifyListeners();

    FlutterBluetoothSerial.instance
        .onStateChanged()
        .listen((event) {
      _isBluetoothEnabled = event == BluetoothState.STATE_ON;
      if (!_isBluetoothEnabled) {
        _devices.clear();
      }
      notifyListeners();
    });
  }

  Future<void> startDiscovery() async {
    try {
      _devices.clear();
      _isScanning = true;
      notifyListeners();

      final stream = FlutterBluetoothSerial.instance.startDiscovery();
      await for (final result in stream) {
        final index = _devices.indexWhere(
          (element) => element.device.address == result.device.address,
        );
        if (index >= 0) {
          _devices[index] = result;
        } else {
          _devices.add(result);
        }
        notifyListeners();
      }
    } catch (e) {
      _error = 'Error en el escaneo: $e';
    } finally {
      _isScanning = false;
      notifyListeners();
    }
  }

  Future<void> enableBluetooth() async {
    try {
      await FlutterBluetoothSerial.instance.requestEnable();
    } catch (e) {
      _error = 'No se pudo activar el Bluetooth: $e';
      notifyListeners();
    }
  }

  Future<void> disableBluetooth() async {
    try {
      await FlutterBluetoothSerial.instance.requestDisable();
    } catch (e) {
      _error = 'No se pudo desactivar el Bluetooth: $e';
      notifyListeners();
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}

class ObdSession extends ChangeNotifier {
  BluetoothConnection? _connection;
  BluetoothDevice? _connectedDevice;
  bool _isBusy = false;
  final List<String> _messages = [];

  BluetoothDevice? get connectedDevice => _connectedDevice;
  bool get isConnected => _connection?.isConnected ?? false;
  bool get isBusy => _isBusy;
  List<String> get messages => List.unmodifiable(_messages);

  String get statusMessage {
    if (_isBusy) return 'Procesando solicitud...';
    if (isConnected && _connectedDevice != null) {
      return 'Conectado a ${_connectedDevice!.name ?? _connectedDevice!.address}';
    }
    return 'Sin conexión activa';
  }

  Future<void> connect(BluetoothDiscoveryResult result) async {
    _setBusy(true);
    try {
      final connection = await BluetoothConnection.toAddress(
        result.device.address,
      );
      _connection = connection;
      _connectedDevice = result.device;
      _messages.clear();
      _messages.add('Conexión establecida, inicializando ELM327...');
      notifyListeners();
      await _initializeObd();
    } catch (e) {
      _messages.add('Error al conectar: $e');
      notifyListeners();
    } finally {
      _setBusy(false);
    }
  }

  Future<void> disconnect() async {
    await _connection?.close();
    _connection = null;
    _connectedDevice = null;
    _messages.add('Conexión finalizada');
    notifyListeners();
  }

  Future<void> _initializeObd() async {
    const commands = [
      'ATZ', // reset
      'ATE0', // eco off
      'ATL0', // linefeeds off
      'ATS0', // spaces off
      'ATH1', // headers on
      'ATSP0', // protocolo automático
    ];
    for (final command in commands) {
      await _writeCommand(command);
      await Future<void>.delayed(const Duration(milliseconds: 300));
    }
    _messages.add('Adaptador inicializado. Listo para consultas.');
    notifyListeners();
  }

  Future<void> fetchVehicleInfo() async {
    await _runObdCommand('0100', description: 'Consultando PIDs soportados...');
    await _runObdCommand('0902', description: 'Leyendo VIN del vehículo...');
  }

  Future<void> fetchTroubleCodes() async {
    await _runObdCommand('03', description: 'Leyendo códigos de falla...');
  }

  Future<void> clearTroubleCodes() async {
    await _runObdCommand('04', description: 'Borrando códigos de falla...');
  }

  Future<void> _runObdCommand(String command, {required String description}) async {
    if (!isConnected || _isBusy) return;
    _setBusy(true);
    _messages.add(description);
    notifyListeners();

    try {
      final response = await _writeCommand(command);
      _messages.add('Respuesta [$command]: $response');
    } catch (e) {
      _messages.add('Error con el comando $command: $e');
    } finally {
      _setBusy(false);
      notifyListeners();
    }
  }

  Future<String> _writeCommand(String command) async {
    final connection = _connection;
    if (connection == null || !connection.isConnected) {
      throw Exception('No hay conexión activa');
    }

    final buffer = StringBuffer(command.trim())..write('\r');
    connection.output.add(Uint8List.fromList(buffer.toString().codeUnits));
    await connection.output.allSent;

    final response = StringBuffer();
    await for (final data in connection.input!) {
      final chunk = String.fromCharCodes(data); // TODO: manejar codificación
      response.write(chunk);
      if (chunk.contains('>')) {
        break;
      }
    }
    final cleaned = response
        .toString()
        .replaceAll(RegExp(r'[\r\n]'), ' ')
        .replaceAll('>', '')
        .trim();
    return cleaned;
  }

  void _setBusy(bool value) {
    _isBusy = value;
    notifyListeners();
  }
}
