import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/company.dart';
import '../../models/device.dart';
import '../../providers/settings_provider.dart';

class DeviceSettings extends StatefulWidget {
  const DeviceSettings({super.key});

  @override
  State<DeviceSettings> createState() => _DeviceSettingsState();
}

class _DeviceSettingsState extends State<DeviceSettings> {
  final _formKey = GlobalKey<FormState>();
  final _deviceIdController = TextEditingController();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  Device? _currentDevice;

  @override
  void initState() {
    super.initState();
    // Ensure devices are loaded when the widget is initialized
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final settingsProvider = Provider.of<SettingsProvider>(context, listen: false);
      if (settingsProvider.selectedCompany != null) {
        settingsProvider.fetchDevices(settingsProvider.selectedCompany!.companyId);
      }
    });
  }

  @override
  void dispose() {
    _deviceIdController.dispose();
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  void _showAddDialog(BuildContext context, String companyId) {
    _deviceIdController.clear();
    _nameController.clear();
    _descriptionController.clear();
    _currentDevice = null;

    showDialog(
      context: context,
      builder: (context) => _buildDeviceDialog(context, isEdit: false, companyId: companyId),
    );
  }

  void _showEditDialog(BuildContext context, Device device) {
    _deviceIdController.text = device.deviceId;
    _nameController.text = device.name ?? '';
    _descriptionController.text = device.description ?? '';
    _currentDevice = device;

    showDialog(
      context: context,
      builder: (context) => _buildDeviceDialog(
        context, 
        isEdit: true, 
        companyId: device.companyId,
      ),
    );
  }

  void _showDeleteDialog(BuildContext context, Device device) {
    _currentDevice = device;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Device'),
        content: Text(
          'Are you sure you want to delete device "${device.name ?? device.deviceId}"?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              _handleDeleteDevice(context);
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  Widget _buildDeviceDialog(BuildContext context, {required bool isEdit, required String companyId}) {
    final title = isEdit ? 'Edit Device' : 'Add Device';
    final buttonText = isEdit ? 'Update' : 'Add';

    return AlertDialog(
      title: Text(title),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
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
              minLines: 2,
              maxLines: 4,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        TextButton(
          onPressed: () {
            if (_formKey.currentState!.validate()) {
              Navigator.of(context).pop();
              if (isEdit) {
                _handleUpdateDevice(context, companyId);
              } else {
                _handleAddDevice(context, companyId);
              }
            }
          },
          child: Text(buttonText),
        ),
      ],
    );
  }

  Future<void> _handleAddDevice(BuildContext context, String companyId) async {
    final settingsProvider = Provider.of<SettingsProvider>(context, listen: false);
    
    final deviceId = _deviceIdController.text.trim();
    final name = _nameController.text.trim();
    final description = _descriptionController.text.trim();
    
    await settingsProvider.addDevice(deviceId, name, description, companyId);
  }

  Future<void> _handleUpdateDevice(BuildContext context, String companyId) async {
    if (_currentDevice == null) return;
    
    final settingsProvider = Provider.of<SettingsProvider>(context, listen: false);
    
    final deviceId = _currentDevice!.deviceId;
    final name = _nameController.text.trim();
    final description = _descriptionController.text.trim();
    
    await settingsProvider.updateDevice(deviceId, name, description, companyId);
  }

  Future<void> _handleDeleteDevice(BuildContext context) async {
    if (_currentDevice == null) return;
    
    final settingsProvider = Provider.of<SettingsProvider>(context, listen: false);
    await settingsProvider.deleteDevice(_currentDevice!.deviceId, _currentDevice!.companyId);
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<SettingsProvider>(
      builder: (context, settingsProvider, _) {
        if (settingsProvider.isLoading) {
          return const Center(child: CircularProgressIndicator());
        }

        return Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Error message
              if (settingsProvider.error.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(bottom: 16.0),
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12.0),
                    decoration: BoxDecoration(
                      color: Colors.red.shade100,
                      borderRadius: BorderRadius.circular(8.0),
                      border: Border.all(color: Colors.red),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.error_outline, color: Colors.red.shade900),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                settingsProvider.error,
                                style: TextStyle(color: Colors.red.shade900, fontWeight: FontWeight.bold),
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.close, size: 20),
                              color: Colors.red.shade900,
                              onPressed: () => settingsProvider.clearError(),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),

              // Company selector
              Padding(
                padding: const EdgeInsets.only(bottom: 16.0),
                child: Row(
                  children: [
                    const Text('Company:', style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _buildCompanyDropdown(settingsProvider),
                    ),
                  ],
                ),
              ),

              // Add device button
              if (settingsProvider.selectedCompany != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 16.0),
                  child: ElevatedButton.icon(
                    onPressed: () => _showAddDialog(context, settingsProvider.selectedCompany!.companyId),
                    icon: const Icon(Icons.add),
                    label: const Text('Add Device'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primary,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ),

              // Devices list
              if (settingsProvider.selectedCompany == null)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(24.0),
                    child: Text(
                      'Please select a company to manage devices.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.grey,
                      ),
                    ),
                  ),
                )
              else if (settingsProvider.devices.isEmpty)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(24.0),
                    child: Text(
                      'No devices found for this company. Click "Add Device" to create one.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.grey,
                      ),
                    ),
                  ),
                )
              else
                Expanded(
                  child: Card(
                    elevation: 2,
                    child: ListView.separated(
                      itemCount: settingsProvider.devices.length,
                      separatorBuilder: (context, index) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final device = settingsProvider.devices[index];
                        return ListTile(
                          title: Text(device.name ?? device.deviceId),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('ID: ${device.deviceId}'),
                              if (device.description != null && device.description!.isNotEmpty)
                                Text(device.description!),
                            ],
                          ),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              IconButton(
                                icon: const Icon(Icons.edit),
                                onPressed: () => _showEditDialog(context, device),
                                tooltip: 'Edit',
                              ),
                              IconButton(
                                icon: const Icon(Icons.delete),
                                onPressed: () => _showDeleteDialog(context, device),
                                tooltip: 'Delete',
                                color: Colors.red,
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildCompanyDropdown(SettingsProvider settingsProvider) {
    if (settingsProvider.companies.isEmpty) {
      return const Text('No companies available', style: TextStyle(fontStyle: FontStyle.italic));
    }

    return DropdownButton<Company>(
      value: settingsProvider.selectedCompany,
      isExpanded: true,
      hint: const Text('Select a company'),
      onChanged: (Company? company) {
        if (company != null) {
          settingsProvider.selectCompany(company);
        }
      },
      items: settingsProvider.companies.map<DropdownMenuItem<Company>>((Company company) {
        return DropdownMenuItem<Company>(
          value: company,
          child: Text(company.name),
        );
      }).toList(),
    );
  }
}
