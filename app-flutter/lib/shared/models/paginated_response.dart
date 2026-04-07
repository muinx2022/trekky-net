import '../../core/utils/json_helpers.dart';

class PaginatedResponse<T> {
  const PaginatedResponse({
    required this.items,
    required this.next,
    required this.count,
  });

  final List<T> items;
  final String? next;
  final int count;

  factory PaginatedResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Map<String, dynamic>) mapper,
  ) {
    return PaginatedResponse<T>(
      items: asList(
        json['results'],
      ).map((item) => mapper(asMap(item))).toList(),
      next: json['next'] as String?,
      count: asType<int>(json['count'], 0),
    );
  }
}
