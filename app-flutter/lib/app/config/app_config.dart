class AppConfig {
  const AppConfig({
    required this.environment,
    required this.apiBaseUrl,
    required this.webBaseUrl,
    required this.oauthCallbackScheme,
    required this.oauthCallbackHost,
  });

  final String environment;
  final String apiBaseUrl;
  final String webBaseUrl;
  final String oauthCallbackScheme;
  final String oauthCallbackHost;

  String get oauthFrontendUrl => '$oauthCallbackScheme://$oauthCallbackHost';

  static const AppConfig current = AppConfig(
    environment: String.fromEnvironment('APP_ENV', defaultValue: 'dev'),
    apiBaseUrl: String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://10.0.2.2:8000',
    ),
    webBaseUrl: String.fromEnvironment(
      'WEB_BASE_URL',
      defaultValue: 'http://localhost:3001',
    ),
    oauthCallbackScheme: String.fromEnvironment(
      'OAUTH_CALLBACK_SCHEME',
      defaultValue: 'trekky',
    ),
    oauthCallbackHost: String.fromEnvironment(
      'OAUTH_CALLBACK_HOST',
      defaultValue: 'auth',
    ),
  );
}
