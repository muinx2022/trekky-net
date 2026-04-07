import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/auth/session_controller.dart';
import '../../home_feed/presentation/home_feed_page.dart';
import '../data/auth_repository_impl.dart';

class AuthPage extends ConsumerStatefulWidget {
  const AuthPage({super.key});

  @override
  ConsumerState<AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends ConsumerState<AuthPage> {
  final _loginEmail = TextEditingController();
  final _loginPassword = TextEditingController();
  final _registerEmail = TextEditingController();
  final _registerUsername = TextEditingController();
  final _registerPassword = TextEditingController();
  final _forgotEmail = TextEditingController();

  bool _loading = false;
  String? _message;

  @override
  void dispose() {
    _loginEmail.dispose();
    _loginPassword.dispose();
    _registerEmail.dispose();
    _registerUsername.dispose();
    _registerPassword.dispose();
    _forgotEmail.dispose();
    super.dispose();
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      await action();
      if (mounted && ref.read(sessionControllerProvider) != null) {
        context.go('/');
      }
    } catch (error) {
      setState(() => _message = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(title: const Text('Tai khoan Trekky')),
        body: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Text(
              'Dang nhap de thich, bao cao, binh luan va dong bo ho so giua Android va iOS.',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 20),
            if (_message != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Text(
                  _message!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            FilledButton.icon(
              onPressed: _loading
                  ? null
                  : () async {
                      final uri = ref
                          .read(authRepositoryProvider)
                          .buildGoogleAuthUrl();
                      await launchUrl(
                        uri,
                        mode: LaunchMode.externalApplication,
                      );
                    },
              icon: const Icon(Icons.login),
              label: const Text('Dang nhap voi Google'),
            ),
            const SizedBox(height: 16),
            const TabBar(
              tabs: [
                Tab(text: 'Dang nhap'),
                Tab(text: 'Dang ky'),
                Tab(text: 'Quen mat khau'),
              ],
            ),
            SizedBox(
              height: 520,
              child: TabBarView(
                children: [
                  _AuthFormCard(
                    title: 'Dang nhap bang email',
                    loading: _loading,
                    children: [
                      TextField(
                        controller: _loginEmail,
                        decoration: const InputDecoration(labelText: 'Email'),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _loginPassword,
                        obscureText: true,
                        decoration: const InputDecoration(
                          labelText: 'Mat khau',
                        ),
                      ),
                      const SizedBox(height: 16),
                      FilledButton(
                        onPressed: _loading
                            ? null
                            : () => _run(() async {
                                await ref
                                    .read(sessionControllerProvider.notifier)
                                    .login(
                                      email: _loginEmail.text.trim(),
                                      password: _loginPassword.text,
                                    );
                              }),
                        child: const Text('Dang nhap'),
                      ),
                    ],
                  ),
                  _AuthFormCard(
                    title: 'Tao tai khoan moi',
                    loading: _loading,
                    children: [
                      TextField(
                        controller: _registerEmail,
                        decoration: const InputDecoration(labelText: 'Email'),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _registerUsername,
                        decoration: const InputDecoration(
                          labelText: 'Username',
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _registerPassword,
                        obscureText: true,
                        decoration: const InputDecoration(
                          labelText: 'Mat khau',
                        ),
                      ),
                      const SizedBox(height: 16),
                      FilledButton(
                        onPressed: _loading
                            ? null
                            : () => _run(() async {
                                await ref
                                    .read(sessionControllerProvider.notifier)
                                    .register(
                                      email: _registerEmail.text.trim(),
                                      username: _registerUsername.text.trim(),
                                      password: _registerPassword.text,
                                    );
                              }),
                        child: const Text('Dang ky'),
                      ),
                    ],
                  ),
                  _AuthFormCard(
                    title: 'Gui link dat lai mat khau',
                    loading: _loading,
                    children: [
                      TextField(
                        controller: _forgotEmail,
                        decoration: const InputDecoration(labelText: 'Email'),
                      ),
                      const SizedBox(height: 16),
                      FilledButton.tonal(
                        onPressed: _loading
                            ? null
                            : () => _run(() async {
                                await ref
                                    .read(sessionControllerProvider.notifier)
                                    .requestPasswordReset(
                                      _forgotEmail.text.trim(),
                                    );
                                setState(() {
                                  _message =
                                      'Neu email ton tai trong he thong, huong dan dat lai mat khau da duoc gui.';
                                });
                              }),
                        child: const Text('Gui email khoi phuc'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            const HomeFeedHeroCard(),
          ],
        ),
      ),
    );
  }
}

class _AuthFormCard extends StatelessWidget {
  const _AuthFormCard({
    required this.title,
    required this.loading,
    required this.children,
  });

  final String title;
  final bool loading;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(top: 20),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ),
                if (loading)
                  const SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(),
                  ),
              ],
            ),
            const SizedBox(height: 16),
            ...children,
          ],
        ),
      ),
    );
  }
}
