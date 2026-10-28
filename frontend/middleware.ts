import createMiddleware from 'next-intl/middleware';
import {routing} from './i18n/routing';

export default createMiddleware(routing);

export const config = {
  // Match all pathnames except for
  // - /api, /media
  // - Next.js internals (_next, etc.)
  // - files with an extension (e.g. favicon.ico, images)
  matcher: ['/((?!api|media|_next|_vercel|.*\\..*).*)'],
};