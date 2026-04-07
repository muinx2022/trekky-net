import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/models/category.dart';
import '../../../shared/models/tag.dart';
import '../../home_feed/data/posts_repository_impl.dart';
import '../../../shared/models/post_summary.dart';
import '../data/taxonomy_repository_impl.dart';

final categoriesProvider = FutureProvider<List<Category>>((ref) {
  return ref.read(taxonomyRepositoryProvider).fetchCategories();
});

final tagsProvider = FutureProvider<List<Tag>>((ref) {
  return ref.read(taxonomyRepositoryProvider).fetchTags();
});

final categoryPostsProvider = FutureProvider.family<List<PostSummary>, String>((
  ref,
  slug,
) {
  return ref.read(postsRepositoryProvider).fetchPostsByCategorySlug(slug);
});

final tagPostsProvider = FutureProvider.family<List<PostSummary>, String>((
  ref,
  slug,
) {
  return ref.read(postsRepositoryProvider).fetchPostsByTagSlug(slug);
});

final userPostsProvider = FutureProvider.family<List<PostSummary>, String>((
  ref,
  username,
) {
  return ref.read(postsRepositoryProvider).fetchPostsByUser(username);
});
