// Fixture for AR003 (class exact + suffix + method + function), AR004 (Proxy/Reflect), AR008 (long line).
// Expected AR003 hits:
//   - class Manager (exact)
//   - class OrderManager (suffix)
//   - class PaymentService (suffix)
//   - class ServiceWorker (NOT flagged — prefix match, excluded)
//   - function doStuff (exact)
//   - method process (inside OrderManager body)

export class Manager {
  process(data: any) {
    return data;
  }
}

export class OrderManager {
  handle(req: any) {
    return req;
  }
}

export class PaymentService {}

export class ServiceWorker {}

export function doStuff(x: any, y: any) {
  return x + y;
}

// AR004 — Proxy and Reflect
const handler = {
  get(target: any, prop: string) {
    return Reflect.get(target, prop);
  },
};

export const dynamic = new Proxy({}, handler);

// AR008 — very long line (minified blob simulated)
export const MINIFIED = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
