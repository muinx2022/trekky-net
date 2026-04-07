import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/widgets/app_async_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../home_feed/presentation/home_feed_page.dart';
import 'taxonomy_controller.dart';

class UserPostsPage extends ConsumerWidget {
  const UserPostsPage({super.key, required this.username});

  final String username;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final posts = ref.watch(userPostsProvider(username));
    return Scaffold(
      appBar: AppBar(title: Text('@$username')),
      body: AppAsyncView(
        value: posts,
        onRetry: () => ref.invalidate(userPostsProvider(username)),
        builder: (items) {
          if (items.isEmpty) {
            return EmptyState(
              title: 'Chua co bai viet cong khai',
              message: '@$username chua co bai viet xuat ban.',
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
