import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/di/providers.dart';
import 'api_client.dart';
import 'auth_interceptor.dart';

final rawDioProvider = Provider<Dio>((ref) {
  final config = ref.read(appConfigProvider);
  return Dio(
    BaseOptions(
      baseUrl: '${config.apiBaseUrl}/api/v1',
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 20),
      sendTimeout: const Duration(seconds: 20),
      contentType: 'application/json',
      responseType: ResponseType.json,
    ),
  );
});

final authenticatedDioProvider = Provider<Dio>((ref) {
  final dio = ref.watch(rawDioProvider);
  dio.interceptors.add(LogInterceptor(requestBody: true, responseBody: false));
  dio.interceptors.add(AuthInterceptor(ref, dio));
  return dio;
});

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(ref.watch(authenticatedDioProvider));
});
