import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/auth/session_controller.dart';
import '../../features/auth/presentation/auth_deep_link_listener.dart';
import '../app_widget.dart';

class TrekkyBootstrap extends ConsumerStatefulWidget {
  const TrekkyBootstrap({super.key});

  @override
  ConsumerState<TrekkyBootstrap> createState() => _TrekkyBootstrapState();
}

class _TrekkyBootstrapState extends ConsumerState<TrekkyBootstrap> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() async {
      await ref.read(sessionControllerProvider.notifier).restoreSession();
      ref.read(authDeepLinkListenerProvider).start();
    });
  }

  @override
  Widget build(BuildContext context) {
    return const TrekkyApp();
  }
}
