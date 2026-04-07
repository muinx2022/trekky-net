import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/widgets/app_async_view.dart';
import 'taxonomy_controller.dart';

class TaxonomyHubPage extends ConsumerWidget {
  const TaxonomyHubPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Browse'),
          bottom: const TabBar(
            tabs: [
              Tab(text: 'Categories'),
              Tab(text: 'Tags'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            AppAsyncView(
              value: ref.watch(categoriesProvider),
              onRetry: () => ref.invalidate(categoriesProvider),
              builder: (categories) => ListView.builder(
                itemCount: categories.length,
                itemBuilder: (context, index) {
                  final category = categories[index];
                  return ListTile(
                    title: Text(category.name),
                    subtitle: category.description == null
                        ? null
                        : Text(category.description!),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => context.push('/categories/${category.slug}'),
                  );
                },
              ),
            ),
            AppAsyncView(
              value: ref.watch(tagsProvider),
              onRetry: () => ref.invalidate(tagsProvider),
              builder: (tags) => ListView.builder(
                itemCount: tags.length,
                itemBuilder: (context, index) {
                  final tag = tags[index];
                  return ListTile(
                    title: Text('#${tag.name}'),
                    subtitle: tag.description == null
                        ? null
                        : Text(tag.description!),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => context.push('/tags/${tag.slug}'),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
