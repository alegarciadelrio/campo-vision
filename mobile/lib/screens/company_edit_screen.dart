import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/company.dart';
import '../providers/settings_provider.dart';

class CompanyEditScreen extends StatefulWidget {
  final Company? company;
  
  const CompanyEditScreen({super.key, this.company});

  @override
  State<CompanyEditScreen> createState() => _CompanyEditScreenState();
}

class _CompanyEditScreenState extends State<CompanyEditScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  bool _isLoading = false;

  bool get isEdit => widget.company != null;

  @override
  void initState() {
    super.initState();
    if (isEdit) {
      _nameController.text = widget.company!.name;
      _descriptionController.text = widget.company!.description ?? '';
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _saveCompany() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    
    final settingsProvider = Provider.of<SettingsProvider>(context, listen: false);
    final name = _nameController.text.trim();
    final description = _descriptionController.text.trim();
    
    bool success;
    if (isEdit) {
      success = await settingsProvider.updateCompany(
        widget.company!.companyId, 
        name, 
        description
      );
    } else {
      success = await settingsProvider.addCompany(name, description);
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
        title: Text(isEdit ? 'Edit Company' : 'Add Company'),
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
                    controller: _nameController,
                    decoration: const InputDecoration(
                      labelText: 'Company Name*',
                      border: OutlineInputBorder(),
                    ),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Please enter a company name';
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
                    onPressed: _isLoading ? null : _saveCompany,
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Text(isEdit ? 'Update Company' : 'Add Company'),
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
