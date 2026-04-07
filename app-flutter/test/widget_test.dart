import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:app_flutter/app/app_widget.dart';
import 'package:app_flutter/features/home_feed/data/posts_repository_impl.dart';
import 'package:app_flutter/features/home_feed/domain/posts_repository.dart';
import 'package:app_flutter/shared/models/paginated_response.dart';
import 'package:app_flutter/shared/models/post_summary.dart';

void main() {
  testWidgets('renders trekky app shell', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          postsRepositoryProvider.overrideWithValue(_FakePostsRepository()),
        ],
        child: const TrekkyApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Trekky'), findsOneWidget);
  });
}

class _FakePostsRepository implements PostsRepository {
  @override
  Future<PaginatedResponse<PostSummary>> fetchHomeFeed() async {
    return const PaginatedResponse<PostSummary>(
      items: [],
      next: null,
      count: 0,
    );
  }

  @override
  Future<PostSummary> fetchPost(String documentId) {
    throw UnimplementedError();
  }

  @override
  Future<List<PostSummary>> fetchPostsByCategorySlug(String slug) async =>
      const [];

  @override
  Future<List<PostSummary>> fetchPostsByTagSlug(String slug) async => const [];

  @override
  Future<List<PostSummary>> fetchPostsByUser(String username) async => const [];
}
