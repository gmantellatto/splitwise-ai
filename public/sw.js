/**
 * sw.js — Service Worker mínimo para habilitar "Adicionar à tela inicial".
 * Não faz cache (o app precisa de internet para chamar a API).
 */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {}); // passa tudo para a rede
