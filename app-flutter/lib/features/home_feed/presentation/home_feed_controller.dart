import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/models/paginated_response.dart';
import '../../../shared/models/post_summary.dart';
import '../data/posts_repository_impl.dart';

final homeFeedProvider = FutureProvider<PaginatedResponse<PostSummary>>((ref) {
  return ref.read(postsRepositoryProvider).fetchHomeFeed();
});
