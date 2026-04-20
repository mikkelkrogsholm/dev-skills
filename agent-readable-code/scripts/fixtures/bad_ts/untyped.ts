// Fixture for AR006 in TS — exported functions with missing annotations.

// Untyped param and return
export function createUser(name) {
  return { name };
}

// Typed param but no return type
export function greet(name: string) {
  return `hi ${name}`;
}

// Arrow with untyped param
export const double = (x) => x * 2;

// Arrow with defaulted param (acceptable — TS infers type) and explicit return type
export const add = (x: number, y: number = 0): number => x + y;

// Fully typed — should NOT trigger
export function chargeCustomer(customerId: string, amountCents: number): Promise<void> {
  return Promise.resolve();
}

// Destructured untyped
export function saveOrder({ id, total }) {
  return { id, total };
}

// Rest param typed
export function joinStrings(sep: string, ...parts: string[]): string {
  return parts.join(sep);
}
