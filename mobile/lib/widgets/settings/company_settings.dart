import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/company.dart';
import '../../providers/settings_provider.dart';

class CompanySettings extends StatefulWidget {
  const CompanySettings({super.key});

  @override
  State<CompanySettings> createState() => _CompanySettingsState();
}

class _CompanySettingsState extends State<CompanySettings> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  Company? _currentCompany;

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  void _showAddDialog(BuildContext context) {
    _nameController.clear();
    _descriptionController.clear();
    _currentCompany = null;

    showDialog(
      context: context,
      builder: (context) => _buildCompanyDialog(context, isEdit: false),
    );
  }

  void _showEditDialog(BuildContext context, Company company) {
    _nameController.text = company.name;
    _descriptionController.text = company.description ?? '';
    _currentCompany = company;

    showDialog(
      context: context,
      builder: (context) => _buildCompanyDialog(context, isEdit: true),
    );
  }

  void _showDeleteDialog(BuildContext context, Company company) {
    _currentCompany = company;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Company'),
        content: Text(
          'Are you sure you want to delete "${company.name}"? This will also delete all devices associated with this company.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              _handleDeleteCompany(context);
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  Widget _buildCompanyDialog(BuildContext context, {required bool isEdit}) {
    final title = isEdit ? 'Edit Company' : 'Add Company';
    final buttonText = isEdit ? 'Update' : 'Add';

    return AlertDialog(
      title: Text(title),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
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
                _handleUpdateCompany(context);
              } else {
                _handleAddCompany(context);
              }
            }
          },
          child: Text(buttonText),
        ),
      ],
    );
  }

  Future<void> _handleAddCompany(BuildContext context) async {
    final settingsProvider = Provider.of<SettingsProvider>(context, listen: false);
    
    final name = _nameController.text.trim();
    final description = _descriptionController.text.trim();
    
    await settingsProvider.addCompany(name, description);
  }

  Future<void> _handleUpdateCompany(BuildContext context) async {
    if (_currentCompany == null) return;
    
    final settingsProvider = Provider.of<SettingsProvider>(context, listen: false);
    
    final name = _nameController.text.trim();
    final description = _descriptionController.text.trim();
    
    await settingsProvider.updateCompany(_currentCompany!.companyId, name, description);
  }

  Future<void> _handleDeleteCompany(BuildContext context) async {
    if (_currentCompany == null) return;
    
    final settingsProvider = Provider.of<SettingsProvider>(context, listen: false);
    await settingsProvider.deleteCompany(_currentCompany!.companyId);
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
                    child: Text(
                      settingsProvider.error,
                      style: TextStyle(color: Colors.red.shade900),
                    ),
                  ),
                ),

              // Add company button
              Padding(
                padding: const EdgeInsets.only(bottom: 16.0),
                child: ElevatedButton.icon(
                  onPressed: () => _showAddDialog(context),
                  icon: const Icon(Icons.add),
                  label: const Text('Add Company'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.primary,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),

              // Companies list
              if (settingsProvider.companies.isEmpty)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(24.0),
                    child: Text(
                      'No companies found. Click "Add Company" to create one.',
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
                      itemCount: settingsProvider.companies.length,
                      separatorBuilder: (context, index) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final company = settingsProvider.companies[index];
                        return ListTile(
                          title: Text(company.name),
                          subtitle: company.description != null && company.description!.isNotEmpty
                              ? Text(company.description!)
                              : null,
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              IconButton(
                                icon: const Icon(Icons.edit),
                                onPressed: () => _showEditDialog(context, company),
                                tooltip: 'Edit',
                              ),
                              IconButton(
                                icon: const Icon(Icons.delete),
                                onPressed: () => _showDeleteDialog(context, company),
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
}
