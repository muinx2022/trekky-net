import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/session_controller.dart';

class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor(this.ref, this.dio);

  final Ref ref;
  final Dio dio;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final session = ref.read(sessionControllerProvider);
    if (session != null && options.headers['Authorization'] == null) {
      options.headers['Authorization'] = 'Bearer ${session.accessToken}';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode != 401) {
      handler.next(err);
      return;
    }

    final request = err.requestOptions;
    if (request.extra['retried'] == true) {
      handler.next(err);
      return;
    }

    final token = await ref
        .read(sessionControllerProvider.notifier)
        .refreshToken();
    if (token == null) {
      handler.next(err);
      return;
    }

    request.headers['Authorization'] = 'Bearer $token';
    request.extra['retried'] = true;

    final response = await dio.fetch<dynamic>(request);
    handler.resolve(response);
  }
}
