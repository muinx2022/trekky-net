import '../../../shared/models/category.dart';
import '../../../shared/models/tag.dart';

abstract class TaxonomyRepository {
  Future<List<Category>> fetchCategories();

  Future<List<Tag>> fetchTags();

  Future<Category> fetchCategoryBySlug(String slug);

  Future<Tag> fetchTagBySlug(String slug);
}
