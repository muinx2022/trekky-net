import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/widgets/empty_state.dart';
import '../../../shared/models/search_suggestions.dart';
import '../data/search_repository_impl.dart';

final searchQueryProvider = StateProvider<String>((ref) => '');

final searchResultsProvider = FutureProvider<SearchSuggestions>((ref) async {
  final query = ref.watch(searchQueryProvider);
  if (query.trim().isEmpty) return const SearchSuggestions();
  return ref.read(searchRepositoryProvider).search(query);
});

class SearchPage extends ConsumerStatefulWidget {
  const SearchPage({super.key});

  @override
  ConsumerState<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends ConsumerState<SearchPage> {
  final controller = TextEditingController();

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final results = ref.watch(searchResultsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Search Trekky')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: controller,
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search),
              hintText: 'Tim bai viet, tag, category...',
            ),
            onChanged: (value) =>
                ref.read(searchQueryProvider.notifier).state = value,
          ),
          const SizedBox(height: 16),
          results.when(
            data: (data) {
              final hasData =
                  data.posts.isNotEmpty ||
                  data.tags.isNotEmpty ||
                  data.categories.isNotEmpty;
              if (!hasData) {
                return const SizedBox(
                  height: 240,
                  child: EmptyState(
                    title: 'Bat dau tim kiem',
                    message: 'Nhap tu khoa de lay goi y tu API public/search.',
                  ),
                );
              }
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _SearchSection(
                    title: 'Posts',
                    children: data.posts
                        .map(
                          (item) => ListTile(
                            title: Text(item.title ?? item.slug),
                            subtitle: item.excerpt == null
                                ? null
                                : Text(item.excerpt!),
                            onTap: () =>
                                context.push('/posts/${item.documentId}'),
                          ),
                        )
                        .toList(),
                  ),
                  _SearchSection(
                    title: 'Categories',
                    children: data.categories
                        .map(
                          (item) => ListTile(
                            title: Text(item.name ?? item.slug),
                            onTap: () =>
                                context.push('/categories/${item.slug}'),
                          ),
                        )
                        .toList(),
                  ),
                  _SearchSection(
                    title: 'Tags',
                    children: data.tags
                        .map(
                          (item) => ListTile(
                            title: Text(item.name ?? item.slug),
                            onTap: () => context.push('/tags/${item.slug}'),
                          ),
                        )
                        .toList(),
                  ),
                ],
              );
            },
            loading: () => const Padding(
              padding: EdgeInsets.all(32),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (error, stackTrace) => Padding(
              padding: const EdgeInsets.all(24),
              child: Text(error.toString()),
            ),
          ),
        ],
      ),
    );
  }
}

class _SearchSection extends StatelessWidget {
  const _SearchSection({required this.title, required this.children});

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    if (children.isEmpty) return const SizedBox.shrink();
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 8, 8, 0),
              child: Text(
                title,
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
            ...children,
          ],
        ),
      ),
    );
  }
}
