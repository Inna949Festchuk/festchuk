'use client';

import {useEffect} from 'react';

/**
 * Управляет CSS-переменной --hud-bottom для плеера и нейро-помощника.
 * Внизу страницы (когда футер виден) элементы плавно поднимаются
 * над видимой частью футера, в остальное время держатся в углу экрана.
 */
export default function HudBottomGuard() {
  useEffect(() => {
    const footer = document.querySelector('footer');
    if (!footer) return;

    const update = () => {
      const corner = window.innerWidth <= 640 ? 12 : 20;
      const rect = footer.getBoundingClientRect();
      const visibleFooter = Math.min(rect.height, Math.max(0, window.innerHeight - rect.top));
      const bottom = visibleFooter > 0 ? visibleFooter + 12 : corner;
      document.documentElement.style.setProperty('--hud-bottom', `${bottom}px`);
    };

    update();
    window.addEventListener('scroll', update, {passive: true});
    window.addEventListener('resize', update, {passive: true});

    return () => {
      window.removeEventListener('scroll', update);
      window.removeEventListener('resize', update);
    };
  }, []);

  return null;
}