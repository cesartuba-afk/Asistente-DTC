import 'dart:async';
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
          if (session.realtimeReadings.isNotEmpty) ...[
            const Divider(height: 24),
            Text(
              'Datos en tiempo real (${session.realtimeReadings.length} sensores)',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            _RealtimeDataGrid(readings: session.realtimeReadings),
          ],
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
  final Set<String> _supportedPids = <String>{};
  final Map<String, ObdSensorReading> _realtimeReadings = {};
  final List<ObdPid> _activeRealtimePids = [];
  Timer? _realtimeTimer;
  bool _isPollingRealtime = false;
  int _realtimeIndex = 0;

  BluetoothDevice? get connectedDevice => _connectedDevice;
  bool get isConnected => _connection?.isConnected ?? false;
  bool get isBusy => _isBusy;
  List<String> get messages => List.unmodifiable(_messages);
  List<ObdSensorReading> get realtimeReadings =>
      List.unmodifiable(_activeRealtimePids.map(
    (pid) => _realtimeReadings[pid.command] ??
        ObdSensorReading(pid: pid, timestamp: DateTime.now()),
  ));

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
      await _discoverSupportedPids();
      _startRealtimeMonitoring();
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
    _supportedPids.clear();
    _realtimeReadings.clear();
    _activeRealtimePids.clear();
    _stopRealtimeMonitoring();
    _messages.add('Conexión finalizada');
    notifyListeners();
  }

  @override
  void dispose() {
    _stopRealtimeMonitoring();
    super.dispose();
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

  Future<void> _discoverSupportedPids() async {
    _supportedPids.clear();
    _activeRealtimePids.clear();
    _realtimeReadings.clear();

    const pidRanges = [
      _PidRange(command: '0100', startPid: 0x00),
      _PidRange(command: '0120', startPid: 0x20),
      _PidRange(command: '0140', startPid: 0x40),
      _PidRange(command: '0160', startPid: 0x60),
    ];

    for (final range in pidRanges) {
      try {
        final dataBytes = await _readObdDataBytes(range.command);
        _supportedPids.addAll(_parseSupportedPids(range.startPid, dataBytes));
      } catch (_) {
        // Ignoramos errores individuales para continuar con otras consultas.
      }
    }

    for (final pid in ObdPid.commonSensors) {
      if (_supportedPids.contains(pid.pid)) {
        _activeRealtimePids.add(pid);
        _realtimeReadings[pid.command] =
            ObdSensorReading(pid: pid, timestamp: DateTime.now());
      }
    }

    if (_activeRealtimePids.isEmpty) {
      _messages.add(
        'No se identificaron sensores en tiempo real soportados por el vehículo.',
      );
    } else {
      _messages.add(
        'Monitoreando ${_activeRealtimePids.length} sensores en tiempo real a 5 lecturas por segundo.',
      );
    }
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

  Future<List<int>> _readObdDataBytes(String command) async {
    final response = await _writeCommand(command);
    final mode = int.parse(command.substring(0, 2), radix: 16);
    final pid = int.parse(command.substring(2, 4), radix: 16);
    final expectedMode = mode + 0x40;
    final bytes = _extractDataBytes(response, expectedMode, pid);
    if (bytes == null) {
      throw Exception('Sin datos válidos para $command');
    }
    return bytes;
  }

  List<int>? _extractDataBytes(String response, int expectedMode, int expectedPid) {
    final tokens = response
        .split(RegExp(r'\s+'))
        .where((token) => token.isNotEmpty)
        .toList();
    final bytes = <int>[];
    for (final token in tokens) {
      final normalized = token.replaceAll(RegExp(r'[^0-9A-Fa-f]'), '');
      if (normalized.length == 2) {
        final value = int.tryParse(normalized, radix: 16);
        if (value != null) {
          bytes.add(value);
        }
      }
    }

    for (var i = 0; i < bytes.length - 1; i++) {
      if (bytes[i] == expectedMode && bytes[i + 1] == expectedPid) {
        return bytes.sublist(i + 2);
      }
    }
    return null;
  }

  Set<String> _parseSupportedPids(int startPid, List<int> dataBytes) {
    final supported = <String>{};
    for (var byteIndex = 0; byteIndex < dataBytes.length; byteIndex++) {
      final byte = dataBytes[byteIndex];
      for (var bit = 0; bit < 8; bit++) {
        final isSupported = (byte & (1 << (7 - bit))) != 0;
        if (isSupported) {
          final pidValue = startPid + byteIndex * 8 + bit + 1;
          supported.add(pidValue.toRadixString(16).padLeft(2, '0').toUpperCase());
        }
      }
    }
    return supported;
  }

  void _startRealtimeMonitoring() {
    _stopRealtimeMonitoring();
    if (_activeRealtimePids.isEmpty) {
      return;
    }
    _realtimeIndex = 0;
    _realtimeTimer =
        Timer.periodic(const Duration(milliseconds: 200), (_) => _pollNextPid());
  }

  void _stopRealtimeMonitoring() {
    _realtimeTimer?.cancel();
    _realtimeTimer = null;
    _isPollingRealtime = false;
  }

  Future<void> _pollNextPid() async {
    if (_isPollingRealtime || !isConnected || _activeRealtimePids.isEmpty) {
      return;
    }
    _isPollingRealtime = true;
    final pid = _activeRealtimePids[_realtimeIndex];
    _realtimeIndex = (_realtimeIndex + 1) % _activeRealtimePids.length;

    try {
      final dataBytes = await _readObdDataBytes(pid.command);
      final value = pid.parse(dataBytes);
      _realtimeReadings[pid.command] = ObdSensorReading(
        pid: pid,
        value: value,
        timestamp: DateTime.now(),
      );
    } catch (e) {
      _realtimeReadings[pid.command] = ObdSensorReading(
        pid: pid,
        error: 'No disponible',
        timestamp: DateTime.now(),
      );
    } finally {
      _isPollingRealtime = false;
      notifyListeners();
    }
  }

  void _setBusy(bool value) {
    _isBusy = value;
    notifyListeners();
  }
}

class _RealtimeDataGrid extends StatelessWidget {
  const _RealtimeDataGrid({required this.readings});

  final List<ObdSensorReading> readings;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: readings
          .map(
            (reading) => SizedBox(
              width: 160,
              child: Card(
                color: colorScheme.surface,
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 16,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        reading.pid.label,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        reading.displayValue,
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                              fontWeight: FontWeight.bold,
                            ) ??
                            const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      if (reading.pid.unit != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          reading.pid.unit!,
                          style: Theme.of(context)
                              .textTheme
                              .labelMedium
                              ?.copyWith(color: colorScheme.primary),
                        ),
                      ],
                      if (reading.errorMessage != null) ...[
                        const SizedBox(height: 6),
                        Text(
                          reading.errorMessage!,
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(color: colorScheme.error),
                        ),
                      ] else ...[
                        const SizedBox(height: 6),
                        Text(
                          'Actualizado ${_formatTimestamp(reading.timestamp)}',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          )
          .toList(),
    );
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);
    if (difference.inSeconds >= 1) {
      return 'hace ${difference.inSeconds}s';
    }
    return 'hace ${difference.inMilliseconds}ms';
  }
}

class ObdSensorReading {
  ObdSensorReading({
    required this.pid,
    this.value,
    this.error,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  final ObdPid pid;
  final double? value;
  final String? error;
  final DateTime timestamp;

  bool get hasValue => value != null;
  bool get hasError => error != null;
  String? get errorMessage => hasError ? error : null;

  String get displayValue {
    if (!hasValue) {
      return '--';
    }
    return pid.formatValue(value!);
  }
}

class ObdPid {
  const ObdPid({
    required this.pid,
    required this.label,
    this.unit,
    required this.parser,
    this.decimals = 1,
  });

  final String pid;
  final String label;
  final String? unit;
  final double? Function(List<int> data) parser;
  final int decimals;

  String get command => '01$pid';

  static List<ObdPid> get commonSensors => const [
        ObdPid(
          pid: '04',
          label: 'Carga del motor',
          unit: '%',
          parser: _requireSingleBytePercentage,
          decimals: 0,
        ),
        ObdPid(
          pid: '05',
          label: 'Temp. refrigerante',
          unit: '°C',
          parser: _requireSingleByteWithOffsetMinus40,
          decimals: 0,
        ),
        ObdPid(
          pid: '0B',
          label: 'Presión colector',
          unit: 'kPa',
          parser: _requireSingleByte,
          decimals: 0,
        ),
        ObdPid(
          pid: '0C',
          label: 'RPM motor',
          unit: 'rpm',
          parser: _parseRpm,
          decimals: 0,
        ),
        ObdPid(
          pid: '0D',
          label: 'Velocidad',
          unit: 'km/h',
          parser: _requireSingleByte,
          decimals: 0,
        ),
        ObdPid(
          pid: '0F',
          label: 'Temp. aire admisión',
          unit: '°C',
          parser: _requireSingleByteWithOffsetMinus40,
          decimals: 0,
        ),
        ObdPid(
          pid: '10',
          label: 'Flujo de aire MAF',
          unit: 'g/s',
          parser: _parseMaf,
          decimals: 2,
        ),
        ObdPid(
          pid: '11',
          label: 'Posición acelerador',
          unit: '%',
          parser: _requireSingleBytePercentage,
          decimals: 0,
        ),
        ObdPid(
          pid: '2F',
          label: 'Nivel de combustible',
          unit: '%',
          parser: _requireSingleBytePercentage,
          decimals: 0,
        ),
      ];

  String formatValue(double value) => value.toStringAsFixed(decimals);

  double? parse(List<int> data) => parser(data);
}

double? _requireSingleByte(List<int> data) {
  if (data.isEmpty) return null;
  return data[0].toDouble();
}

double? _requireSingleBytePercentage(List<int> data) {
  if (data.isEmpty) return null;
  return data[0] * 100 / 255;
}

double? _requireSingleByteWithOffsetMinus40(List<int> data) {
  if (data.isEmpty) return null;
  return data[0] - 40;
}

double? _parseRpm(List<int> data) {
  if (data.length < 2) return null;
  return ((data[0] * 256) + data[1]) / 4;
}

double? _parseMaf(List<int> data) {
  if (data.length < 2) return null;
  return ((data[0] * 256) + data[1]) / 100;
}

class _PidRange {
  const _PidRange({required this.command, required this.startPid});

  final String command;
  final int startPid;
}
