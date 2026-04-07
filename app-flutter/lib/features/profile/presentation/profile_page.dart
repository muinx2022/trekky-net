import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/auth/session_controller.dart';
import '../data/profile_repository_impl.dart';

class ProfilePage extends ConsumerStatefulWidget {
  const ProfilePage({super.key});

  @override
  ConsumerState<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends ConsumerState<ProfilePage> {
  final _usernameController = TextEditingController();
  final _bioController = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _usernameController.dispose();
    _bioController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionControllerProvider);
    if (session == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Profile')),
        body: Center(
          child: FilledButton(
            onPressed: () => context.go('/auth'),
            child: const Text('Dang nhap'),
          ),
        ),
      );
    }

    _usernameController.text = _usernameController.text.isEmpty
        ? session.user.username
        : _usernameController.text;
    _bioController.text = _bioController.text.isEmpty
        ? (session.user.bio ?? '')
        : _bioController.text;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ho so cua toi'),
        actions: [
          TextButton(
            onPressed: () async {
              final router = GoRouter.of(context);
              await ref.read(sessionControllerProvider.notifier).logout();
              if (!mounted) return;
              router.go('/auth');
            },
            child: const Text('Dang xuat'),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '@${session.user.username}',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(session.user.email),
                  const SizedBox(height: 20),
                  TextField(
                    controller: _usernameController,
                    decoration: const InputDecoration(labelText: 'Username'),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _bioController,
                    minLines: 3,
                    maxLines: 5,
                    decoration: const InputDecoration(labelText: 'Bio'),
                  ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: _saving
                        ? null
                        : () async {
                            final messenger = ScaffoldMessenger.of(context);
                            setState(() => _saving = true);
                            try {
                              final updated = await ref
                                  .read(profileRepositoryProvider)
                                  .updateProfile(
                                    session: session,
                                    username: _usernameController.text.trim(),
                                    bio: _bioController.text.trim(),
                                  );
                              await ref
                                  .read(sessionControllerProvider.notifier)
                                  .updateSession(updated);
                              if (!mounted) return;
                              messenger.showSnackBar(
                                const SnackBar(
                                  content: Text('Da cap nhat ho so.'),
                                ),
                              );
                            } finally {
                              if (mounted) setState(() => _saving = false);
                            }
                          },
                    child: const Text('Luu thay doi'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
