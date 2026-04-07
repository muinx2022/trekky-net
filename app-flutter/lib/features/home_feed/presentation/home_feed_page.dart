import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/di/providers.dart';
import '../../../core/utils/url_utils.dart';
import '../../../core/widgets/app_async_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/network_image_card.dart';
import '../../../shared/models/post_summary.dart';
import 'home_feed_controller.dart';

class HomeFeedPage extends ConsumerWidget {
  const HomeFeedPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final feed = ref.watch(homeFeedProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Trekky')),
      body: AppAsyncView(
        value: feed,
        onRetry: () => ref.invalidate(homeFeedProvider),
        builder: (data) {
          if (data.items.isEmpty) {
            return const EmptyState(
              title: 'Chua co bai viet',
              message:
                  'Hay seed demo data hoac dang bai tu web/admin de kiem tra mobile.',
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.refresh(homeFeedProvider.future),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
              children: [
                const HomeFeedHeroCard(),
                const SizedBox(height: 16),
                ...data.items.map(
                  (post) => Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: PostPreviewCard(
                      post: post,
                      onTap: () => context.push('/posts/${post.documentId}'),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class HomeFeedHeroCard extends StatelessWidget {
  const HomeFeedHeroCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: const LinearGradient(
          colors: [Color(0xFF0F766E), Color(0xFF22C55E)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Kham pha bai viet leo nui, du lich va hiking',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Ban mobile duoc sap xep theo feature ngay tu dau de de them tim kiem, thong bao, offline cache va My Posts sau nay.',
            style: TextStyle(color: Colors.white, height: 1.4),
          ),
        ],
      ),
    );
  }
}

class PostPreviewCard extends ConsumerWidget {
  const PostPreviewCard({super.key, required this.post, required this.onTap});

  final PostSummary post;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final apiBaseUrl = ref.read(appConfigProvider).apiBaseUrl;
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(24),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              NetworkImageCard(
                imageUrl: post.images.isEmpty
                    ? null
                    : resolveUrl(apiBaseUrl, post.images.first.url),
              ),
              const SizedBox(height: 16),
              Text(
                post.title,
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              Text(
                post.excerpt ?? post.content,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if (post.author != null)
                    Chip(label: Text('@${post.author!.username}')),
                  ...post.categories
                      .take(2)
                      .map((category) => Chip(label: Text(category.name))),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
