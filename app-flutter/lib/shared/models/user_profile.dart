import '../../core/utils/json_helpers.dart';
import 'media_asset.dart';

class UserProfile {
  const UserProfile({
    required this.id,
    required this.documentId,
    required this.email,
    required this.username,
    this.role,
    this.bio,
    this.avatarUrl,
  });

  final int id;
  final String documentId;
  final String email;
  final String username;
  final String? role;
  final String? bio;
  final String? avatarUrl;

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    final avatar = json['avatar'];
    String? avatarUrl;
    if (avatar is String) {
      avatarUrl = avatar;
    } else if (avatar is Map<String, dynamic>) {
      avatarUrl = MediaAsset.fromJson(avatar).url;
    }

    return UserProfile(
      id: asType<int>(json['id'], 0),
      documentId: asString(json['documentId'] ?? json['document_id']),
      email: asString(json['email']),
      username: asString(json['username']),
      role: asString(json['role']).isEmpty ? null : asString(json['role']),
      bio: asString(json['bio']).isEmpty ? null : asString(json['bio']),
      avatarUrl: avatarUrl,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'documentId': documentId,
    'email': email,
    'username': username,
    'role': role,
    'bio': bio,
    'avatar': avatarUrl,
  };
}
