// Fixture for AR005 in TS — 5-level chain, expect one finding on User (depth 4).

export class Base {}
class Entity extends Base {}
class Persisted extends Entity {}
class Auditable extends Persisted {}
export class User extends Auditable {}
