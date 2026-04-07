import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/di/providers.dart';
import '../../../core/utils/url_utils.dart';
import '../../../core/widgets/app_async_view.dart';
import '../../../core/widgets/network_image_card.dart';
import '../../comments_interactions/presentation/comments_section.dart';
import '../../home_feed/data/posts_repository_impl.dart';

final postDetailProvider = FutureProvider.family((ref, String documentId) {
  return ref.read(postsRepositoryProvider).fetchPost(documentId);
});

class PostDetailPage extends ConsumerWidget {
  const PostDetailPage({super.key, required this.documentId});

  final String documentId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final post = ref.watch(postDetailProvider(documentId));
    final apiBaseUrl = ref.read(appConfigProvider).apiBaseUrl;

    return Scaffold(
      appBar: AppBar(title: const Text('Chi tiet bai viet')),
      body: AppAsyncView(
        value: post,
        onRetry: () => ref.invalidate(postDetailProvider(documentId)),
        builder: (data) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            NetworkImageCard(
              imageUrl: data.images.isEmpty
                  ? null
                  : resolveUrl(apiBaseUrl, data.images.first.url),
              height: 220,
            ),
            const SizedBox(height: 16),
            Text(
              data.title,
              style: Theme.of(
                context,
              ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            if (data.author != null)
              Text(
                'Tac gia: @${data.author!.username}',
                style: Theme.of(context).textTheme.titleMedium,
              ),
            const SizedBox(height: 16),
            SelectableText(data.content),
            const SizedBox(height: 24),
            CommentsSection(documentId: data.documentId),
          ],
        ),
      ),
    );
  }
}
