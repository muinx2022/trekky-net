import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/widgets/app_async_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../home_feed/presentation/home_feed_page.dart';
import 'taxonomy_controller.dart';

enum TaxonomyKind { category, tag }

class TaxonomyDetailPage extends ConsumerWidget {
  const TaxonomyDetailPage.category({super.key, required this.slug})
    : kind = TaxonomyKind.category;

  const TaxonomyDetailPage.tag({super.key, required this.slug})
    : kind = TaxonomyKind.tag;

  final String slug;
  final TaxonomyKind kind;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final posts = kind == TaxonomyKind.category
        ? ref.watch(categoryPostsProvider(slug))
        : ref.watch(tagPostsProvider(slug));

    return Scaffold(
      appBar: AppBar(
        title: Text(kind == TaxonomyKind.category ? 'Category' : 'Tag'),
      ),
      body: AppAsyncView(
        value: posts,
        onRetry: () {
          if (kind == TaxonomyKind.category) {
            ref.invalidate(categoryPostsProvider(slug));
          } else {
            ref.invalidate(tagPostsProvider(slug));
          }
        },
        builder: (items) {
          if (items.isEmpty) {
            return const EmptyState(
              title: 'Khong co bai viet',
              message: 'Taxonomy nay chua co bai dang xuat ban.',
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: items.length,
            separatorBuilder: (_, _) => const SizedBox(height: 16),
            itemBuilder: (context, index) => PostPreviewCard(
              post: items[index],
              onTap: () => context.push('/posts/${items[index].documentId}'),
            ),
          );
        },
      ),
    );
  }
}
