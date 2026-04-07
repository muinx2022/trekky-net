import '../../core/utils/json_helpers.dart';

class MediaAsset {
  const MediaAsset({
    required this.id,
    required this.url,
    this.altText,
    this.width,
    this.height,
  });

  final int id;
  final String url;
  final String? altText;
  final int? width;
  final int? height;

  factory MediaAsset.fromJson(Map<String, dynamic> json) => MediaAsset(
    id: asType<int>(json['id'], 0),
    url: asString(json['url']),
    altText: asString(json['alt_text']).isEmpty
        ? null
        : asString(json['alt_text']),
    width: json['width'] as int?,
    height: json['height'] as int?,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'url': url,
    'alt_text': altText,
    'width': width,
    'height': height,
  };
}
