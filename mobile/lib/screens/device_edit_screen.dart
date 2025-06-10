import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/device.dart';
import '../providers/settings_provider.dart';

class DeviceEditScreen extends StatefulWidget {
  final Device? device;
  final String companyId;
  
  const DeviceEditScreen({
    super.key, 
    this.device,
    required this.companyId,
  });

  @override
  State<DeviceEditScreen> createState() => _DeviceEditScreenState();
}

class _DeviceEditScreenState extends State<DeviceEditScreen> {
  final _formKey = GlobalKey<FormState>();
  final _deviceIdController = TextEditingController();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  bool _isLoading = false;

  bool get isEdit => widget.device != null;

  @override
  void initState() {
    super.initState();
    if (isEdit) {
      _deviceIdController.text = widget.device!.deviceId;
      _nameController.text = widget.device!.name ?? '';
      _descriptionController.text = widget.device!.description ?? '';
    }
  }

  @override
  void dispose() {
    _deviceIdController.dispose();
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _saveDevice() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    
    final settingsProvider = Provider.of<SettingsProvider>(context, listen: false);
    final deviceId = _deviceIdController.text.trim();
    final name = _nameController.text.trim();
    final description = _descriptionController.text.trim();
    
    bool success;
    if (isEdit) {
      success = await settingsProvider.updateDevice(
        widget.device!.deviceId,
        name,
        description,
        widget.companyId,
      );
    } else {
      success = await settingsProvider.addDevice(
        deviceId,
        name,
        description,
        widget.companyId,
      );
    }
    
    setState(() => _isLoading = false);
    
    if (success && mounted) {
      Navigator.of(context).pop(true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(isEdit ? 'Edit Device' : 'Add Device'),
      ),
      body: Consumer<SettingsProvider>(
        builder: (context, settingsProvider, _) {
          return Padding(
            padding: const EdgeInsets.all(16.0),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Error message
                  if (settingsProvider.error.isNotEmpty)
                    Container(
                      margin: const EdgeInsets.only(bottom: 16.0),
                      padding: const EdgeInsets.all(12.0),
                      decoration: BoxDecoration(
                        color: Colors.red.shade100,
                        borderRadius: BorderRadius.circular(8.0),
                        border: Border.all(color: Colors.red),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.error_outline, color: Colors.red.shade900),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              settingsProvider.error,
                              style: TextStyle(color: Colors.red.shade900),
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.close, size: 20),
                            color: Colors.red.shade900,
                            onPressed: () => settingsProvider.clearError(),
                          ),
                        ],
                      ),
                    ),
                  
                  TextFormField(
                    controller: _deviceIdController,
                    decoration: const InputDecoration(
                      labelText: 'Device ID*',
                      border: OutlineInputBorder(),
                    ),
                    enabled: !isEdit, // Cannot edit device ID
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Please enter a device ID';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _nameController,
                    decoration: const InputDecoration(
                      labelText: 'Device Name*',
                      border: OutlineInputBorder(),
                    ),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Please enter a device name';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _descriptionController,
                    decoration: const InputDecoration(
                      labelText: 'Description',
                      border: OutlineInputBorder(),
                    ),
                    minLines: 3,
                    maxLines: 5,
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _saveDevice,
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Text(isEdit ? 'Update Device' : 'Add Device'),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
