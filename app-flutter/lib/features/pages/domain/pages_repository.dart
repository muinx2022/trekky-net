import '../../../shared/models/page_content.dart';

abstract class PagesRepository {
  Future<PageContent> fetchBySlug(String slug);
}
