class AclEntry {
  final String username;
  final String permissions; // e.g. "rwx"

  AclEntry({required this.username, required this.permissions});

  factory AclEntry.fromJson(Map<String, dynamic> json) => AclEntry(
        username: json["username"],
        permissions: json["permissions"],
      );

  Map<String, dynamic> toJson() => {
        "username": username,
        "permissions": permissions,
      };
}
