import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/di/providers.dart';
import '../../../core/auth/session_controller.dart';

final authDeepLinkListenerProvider = Provider<AuthDeepLinkListener>((ref) {
  return AuthDeepLinkListener(ref, AppLinks());
});

class AuthDeepLinkListener {
  AuthDeepLinkListener(this.ref, this._appLinks);

  final Ref ref;
  final AppLinks _appLinks;
  StreamSubscription<Uri>? _subscription;

  void start() {
    _subscription ??= _appLinks.uriLinkStream.listen((uri) async {
      final config = ref.read(appConfigProvider);
      if (uri.scheme != config.oauthCallbackScheme) return;
      await ref
          .read(sessionControllerProvider.notifier)
          .consumeOAuthCallback(uri);
    });
  }

  Future<void> dispose() async {
    await _subscription?.cancel();
    _subscription = null;
  }
}
