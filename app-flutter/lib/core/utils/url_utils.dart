String? resolveUrl(String? baseUrl, String? rawUrl) {
  if (rawUrl == null || rawUrl.isEmpty) return null;
  if (rawUrl.startsWith('http://') || rawUrl.startsWith('https://')) {
    return rawUrl;
  }
  if (baseUrl == null || baseUrl.isEmpty) return rawUrl;
  final normalizedBase = baseUrl.endsWith('/')
      ? baseUrl.substring(0, baseUrl.length - 1)
      : baseUrl;
  final normalizedPath = rawUrl.startsWith('/') ? rawUrl : '/$rawUrl';
  return '$normalizedBase$normalizedPath';
}
