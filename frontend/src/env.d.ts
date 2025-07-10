/// <reference path="../.astro/types.d.ts" />
/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_API_URL: string;
  readonly PUBLIC_API_VERSION: string;
  readonly PUBLIC_APP_NAME: string;
  readonly PUBLIC_APP_VERSION: string;
  readonly PUBLIC_APP_URL: string;
  readonly PUBLIC_STRIPE_PUBLISHABLE_KEY: string;
  readonly PUBLIC_GA_TRACKING_ID: string;
  readonly PUBLIC_SENTRY_DSN: string;
  readonly PUBLIC_ENABLE_ANALYTICS: string;
  readonly PUBLIC_ENABLE_CHAT_WIDGET: string;
  readonly PUBLIC_ENABLE_DARK_MODE: string;
  readonly PUBLIC_DEBUG: string;
  readonly PUBLIC_GOOGLE_CLIENT_ID: string;
  readonly PUBLIC_FACEBOOK_APP_ID: string;
  readonly PUBLIC_WIDGET_DEFAULT_THEME: string;
  readonly PUBLIC_WIDGET_DEFAULT_POSITION: string;
  readonly PUBLIC_MAX_FILE_SIZE: string;
  readonly PUBLIC_ALLOWED_FILE_TYPES: string;
  readonly PUBLIC_DEFAULT_LOCALE: string;
  readonly PUBLIC_SUPPORTED_LOCALES: string;
  readonly PUBLIC_GOOGLE_MAPS_API_KEY: string;
  readonly PUBLIC_WS_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
