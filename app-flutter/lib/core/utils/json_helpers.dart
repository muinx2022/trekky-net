T asType<T>(Object? value, T fallback) => value is T ? value : fallback;

Map<String, dynamic> asMap(Object? value) =>
    value is Map<String, dynamic> ? value : <String, dynamic>{};

List<dynamic> asList(Object? value) => value is List ? value : <dynamic>[];

String asString(Object? value, [String fallback = '']) =>
    value == null ? fallback : value.toString();
