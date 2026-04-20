// Should trigger AR002 — the error block below is duplicated in refunds.ts.

import { logger } from "./logger";

export async function createOrder(req: any, res: any) {
  try {
    const payload = req.body;
    if (!payload.customer_id) {
      return res.status(400).json({ error: "missing customer_id" });
    }
    return res.status(201).json({ id: "ord_1" });
  } catch (err) {
    logger.error({ err, path: req.path });
    const status = err instanceof SyntaxError ? 400 : 500;
    const message = err instanceof SyntaxError ? err.message : "Internal error";
    res.setHeader("x-correlation-id", req.correlation_id);
    return res.status(status).json({ error: message, correlation: req.correlation_id });
  }
}
