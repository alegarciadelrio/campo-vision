import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/company.dart';
import '../providers/dashboard_provider.dart';

class CompanySelector extends StatelessWidget {
  const CompanySelector({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Consumer<DashboardProvider>(
      builder: (context, dashboardProvider, _) {
        if (dashboardProvider.isLoading) {
          return const Center(
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 16.0),
              child: LinearProgressIndicator(),
            ),
          );
        }

        if (dashboardProvider.companies.isEmpty) {
          return const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16.0),
            child: Text(
              'No companies available',
              style: TextStyle(color: Colors.red),
            ),
          );
        }

        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0),
          child: DropdownButton<String>(
            isExpanded: true,
            value: dashboardProvider.selectedCompany?.companyId,
            hint: const Text('Select a company'),
            onChanged: (String? companyId) {
              if (companyId != null) {
                final company = dashboardProvider.companies.firstWhere(
                  (c) => c.companyId == companyId,
                );
                dashboardProvider.selectCompany(company);
              }
            },
            items: dashboardProvider.companies.map((Company company) {
              return DropdownMenuItem<String>(
                value: company.companyId,
                child: Text(company.name),
              );
            }).toList(),
          ),
        );
      },
    );
  }
}
