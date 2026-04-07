export type Category = {
  id: number;
  documentId: string;
  name: string;
  slug: string;
  description?: string;
  parent?: {
    documentId: string;
    name: string;
    slug: string;
  } | null;
  children?: Category[];
};

export type Tag = {
  id: number;
  documentId: string;
  name: string;
  slug: string;
  description?: string;
  postsCount?: number;
};

export type TagOption = {
  documentId: string;
  name: string;
  slug?: string;
};

export type Comment = {
  id: number;
  documentId: string;
  authorName: string;
  authorAvatarUrl?: string | null;
  content: string;
  targetType: "post" | "page" | "product" | "other";
  targetDocumentId: string;
  createdAt: string;
  parent?: { documentId: string } | null;
};

export type SearchSuggestionHit = {
  id?: number;
  documentId: string;
  title?: string;
  name?: string;
  slug: string;
  excerpt?: string;
  description?: string;
};

export type SearchSuggestions = {
  posts: SearchSuggestionHit[];
  tags: SearchSuggestionHit[];
  categories: SearchSuggestionHit[];
};

export type Media = {
  id: number;
  url: string;
  mime?: string | null;
  alternativeText?: string | null;
  width?: number;
  height?: number;
  name?: string;
};

export type PostAuthor = {
  id: number;
  username: string;
  avatar?: Media | null;
};

export type Post = {
  id: number;
  documentId: string;
  title: string;
  slug: string;
  excerpt?: string;
  content: string;
  categories?: Category[];
  tags?: Tag[];
  images?: Media[];
  author?: PostAuthor;
  createdAt?: string;
  updatedAt?: string;
  publishedAt?: string;
  status?: "draft" | "published";
  commentsCount?: number;
  likesCount?: number;
};

export type StrapiPage = {
  id: number;
  documentId: string;
  title: string;
  slug: string;
  type: "home" | "footer";
  content?: string | null;
};

export type PaginationMeta = {
  page: number;
  pageSize: number;
  pageCount: number;
  total: number;
};

export type PaginatedResponse<T> = {
  data: T[];
  meta: { pagination: PaginationMeta };
};

export type User = {
  id: number;
  email: string;
  username: string;
  bio?: string | null;
  avatarId?: number | null;
  avatarUrl?: string | null;
  avatarVersion?: number;
  jwt: string;
  refreshToken?: string;
};
