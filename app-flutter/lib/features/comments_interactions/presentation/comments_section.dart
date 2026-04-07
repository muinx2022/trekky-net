import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/auth/session_controller.dart';
import '../../../core/widgets/app_async_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../data/comments_repository_impl.dart';
import '../data/interactions_repository_impl.dart';
import 'comments_controller.dart';

class CommentsSection extends ConsumerStatefulWidget {
  const CommentsSection({super.key, required this.documentId});

  final String documentId;

  @override
  ConsumerState<CommentsSection> createState() => _CommentsSectionState();
}

class _CommentsSectionState extends ConsumerState<CommentsSection> {
  final _commentController = TextEditingController();
  bool _submitting = false;

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final comments = ref.watch(commentsProvider(widget.documentId));
    final session = ref.watch(sessionControllerProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text('Binh luan', style: Theme.of(context).textTheme.titleLarge),
            const Spacer(),
            TextButton.icon(
              onPressed: session == null || _submitting
                  ? null
                  : () async {
                      final messenger = ScaffoldMessenger.of(context);
                      await ref
                          .read(interactionsRepositoryProvider)
                          .likePost(widget.documentId);
                      if (!mounted) return;
                      messenger.showSnackBar(
                        const SnackBar(content: Text('Da ghi nhan like.')),
                      );
                    },
              icon: const Icon(Icons.favorite_border),
              label: const Text('Like'),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (session != null)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  TextField(
                    controller: _commentController,
                    minLines: 2,
                    maxLines: 4,
                    decoration: const InputDecoration(
                      hintText: 'Them binh luan cua ban...',
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      OutlinedButton(
                        onPressed: _submitting
                            ? null
                            : () async {
                                final messenger = ScaffoldMessenger.of(context);
                                final reason = await _showReasonDialog(context);
                                if (reason == null || reason.trim().isEmpty) {
                                  return;
                                }
                                await ref
                                    .read(interactionsRepositoryProvider)
                                    .reportPost(
                                      targetDocumentId: widget.documentId,
                                      reason: reason.trim(),
                                    );
                                if (!mounted) return;
                                messenger.showSnackBar(
                                  const SnackBar(
                                    content: Text('Bao cao da duoc gui.'),
                                  ),
                                );
                              },
                        child: const Text('Bao cao bai viet'),
                      ),
                      const Spacer(),
                      FilledButton(
                        onPressed: _submitting
                            ? null
                            : () async {
                                setState(() => _submitting = true);
                                try {
                                  await ref
                                      .read(commentsRepositoryProvider)
                                      .addComment(
                                        targetDocumentId: widget.documentId,
                                        content: _commentController.text.trim(),
                                      );
                                  _commentController.clear();
                                  ref.invalidate(
                                    commentsProvider(widget.documentId),
                                  );
                                } finally {
                                  if (mounted) {
                                    setState(() => _submitting = false);
                                  }
                                }
                              },
                        child: const Text('Gui'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          )
        else
          const Padding(
            padding: EdgeInsets.only(bottom: 12),
            child: Text('Dang nhap de binh luan, like va bao cao noi dung.'),
          ),
        AppAsyncView(
          value: comments,
          onRetry: () => ref.invalidate(commentsProvider(widget.documentId)),
          builder: (items) {
            if (items.isEmpty) {
              return const EmptyState(
                title: 'Chua co binh luan',
                message: 'Hay tro thanh nguoi dau tien de lai y kien.',
              );
            }
            return Column(
              children: items
                  .map(
                    (comment) => Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        title: Text(comment.authorName),
                        subtitle: Text(comment.content),
                      ),
                    ),
                  )
                  .toList(),
            );
          },
        ),
      ],
    );
  }

  Future<String?> _showReasonDialog(BuildContext context) async {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Bao cao bai viet'),
        content: TextField(
          controller: controller,
          minLines: 2,
          maxLines: 4,
          decoration: const InputDecoration(hintText: 'Ly do bao cao'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Huy'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(controller.text),
            child: const Text('Gui'),
          ),
        ],
      ),
    );
  }
}
