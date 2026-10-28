import {getRequestConfig} from 'next-intl/server';
import {defaultLocale, locales} from './routing';

export default getRequestConfig(async ({requestLocale}) => {
  // Allow localizing the app on request (e.g. via a "?locale=en" search
  // parameter or a header). Fallback to the default locale.
  let locale = await requestLocale;

  if (!locale || !locales.includes(locale as (typeof locales)[number])) {
    locale = defaultLocale;
  }

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});