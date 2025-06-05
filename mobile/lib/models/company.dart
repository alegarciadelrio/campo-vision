class Company {
  final String companyId;
  final String name;
  final String? description;
  final String? address;
  final String? contactEmail;
  final String? contactPhone;

  Company({
    required this.companyId,
    required this.name,
    this.description,
    this.address,
    this.contactEmail,
    this.contactPhone,
  });

  factory Company.fromJson(Map<String, dynamic> json) {
    return Company(
      companyId: json['companyId'],
      name: json['name'],
      description: json['description'],
      address: json['address'],
      contactEmail: json['contactEmail'],
      contactPhone: json['contactPhone'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'companyId': companyId,
      'name': name,
      'description': description,
      'address': address,
      'contactEmail': contactEmail,
      'contactPhone': contactPhone,
    };
  }
}
