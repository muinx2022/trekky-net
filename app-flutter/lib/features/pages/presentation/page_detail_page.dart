import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/widgets/app_async_view.dart';
import '../data/pages_repository_impl.dart';

final pageDetailProvider = FutureProvider.family((ref, String slug) {
  return ref.read(pagesRepositoryProvider).fetchBySlug(slug);
});

class PageDetailPage extends ConsumerWidget {
  const PageDetailPage({super.key, required this.slug});

  final String slug;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final page = ref.watch(pageDetailProvider(slug));
    return Scaffold(
      appBar: AppBar(title: const Text('Page')),
      body: AppAsyncView(
        value: page,
        onRetry: () => ref.invalidate(pageDetailProvider(slug)),
        builder: (data) => ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Text(data.title, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 16),
            SelectableText(data.content ?? ''),
          ],
        ),
      ),
    );
  }
}
