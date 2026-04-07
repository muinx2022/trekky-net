import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/auth/session_controller.dart';
import '../../features/auth/presentation/auth_page.dart';
import '../../features/home_feed/presentation/home_feed_page.dart';
import '../../features/pages/presentation/page_detail_page.dart';
import '../../features/post_detail/presentation/post_detail_page.dart';
import '../../features/profile/presentation/profile_page.dart';
import '../../features/search/presentation/search_page.dart';
import '../../features/taxonomy/presentation/taxonomy_detail_page.dart';
import '../../features/taxonomy/presentation/taxonomy_hub_page.dart';
import '../../features/taxonomy/presentation/user_posts_page.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final session = ref.watch(sessionControllerProvider);
  return GoRouter(
    initialLocation: '/',
    routes: [
      ShellRoute(
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          GoRoute(
            path: '/',
            name: 'home',
            builder: (context, state) => const HomeFeedPage(),
          ),
          GoRoute(
            path: '/search',
            name: 'search',
            builder: (context, state) => const SearchPage(),
          ),
          GoRoute(
            path: '/taxonomy',
            name: 'taxonomy',
            builder: (context, state) => const TaxonomyHubPage(),
          ),
          GoRoute(
            path: '/profile',
            name: 'profile',
            builder: (context, state) => const ProfilePage(),
          ),
        ],
      ),
      GoRoute(
        path: '/auth',
        name: 'auth',
        builder: (context, state) => const AuthPage(),
      ),
      GoRoute(
        path: '/posts/:documentId',
        name: 'post-detail',
        builder: (context, state) =>
            PostDetailPage(documentId: state.pathParameters['documentId']!),
      ),
      GoRoute(
        path: '/categories/:slug',
        name: 'category-detail',
        builder: (context, state) =>
            TaxonomyDetailPage.category(slug: state.pathParameters['slug']!),
      ),
      GoRoute(
        path: '/tags/:slug',
        name: 'tag-detail',
        builder: (context, state) =>
            TaxonomyDetailPage.tag(slug: state.pathParameters['slug']!),
      ),
      GoRoute(
        path: '/pages/:slug',
        name: 'page-detail',
        builder: (context, state) =>
            PageDetailPage(slug: state.pathParameters['slug']!),
      ),
      GoRoute(
        path: '/users/:username',
        name: 'user-posts',
        builder: (context, state) =>
            UserPostsPage(username: state.pathParameters['username']!),
      ),
    ],
    redirect: (context, state) {
      final isProfile = state.fullPath == '/profile';
      if (isProfile && session == null) return '/auth';
      return null;
    },
  );
});

class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    final index = switch (location) {
      '/search' => 1,
      '/taxonomy' => 2,
      '/profile' => 3,
      _ => 0,
    };

    return Scaffold(
      body: SafeArea(child: child),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.explore_outlined),
            label: 'Home',
          ),
          NavigationDestination(icon: Icon(Icons.search), label: 'Search'),
          NavigationDestination(
            icon: Icon(Icons.grid_view_rounded),
            label: 'Browse',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            label: 'Profile',
          ),
        ],
        onDestinationSelected: (nextIndex) {
          switch (nextIndex) {
            case 0:
              context.go('/');
            case 1:
              context.go('/search');
            case 2:
              context.go('/taxonomy');
            case 3:
              context.go('/profile');
          }
        },
      ),
    );
  }
}
