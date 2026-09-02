# Code Standards — Agentic Commerce V2

## Engineering Mindset

- Think before implementing.
- Read context files first.
- Scope is sacred.
- Every feature must be testable.
- Prefer clean, boring, readable code.
- One feature at a time.
- Failures must be handled explicitly.
- Do not hide business logic in UI components.

## TypeScript

- `strict: true`.
- Never use `any`.
- Avoid unsafe type assertions.
- Explicitly type public function parameters and returns.
- Prefer `type` for domain objects/unions.
- Use `interface` only when extension is useful.
- Use `const` by default.
- Async operations must handle errors.

## React

- Functional components only.
- Named exports.
- One main component per file.
- Components should focus on presentation and interaction.
- API calls belong in query hooks/services, not scattered through JSX.
- Use TanStack Query for server state.
- Use local state only for local UI state.
- Keep authoritative commerce state on the backend.
- Do not duplicate quote calculation in React.

## Folder Structure

```text
frontend/
  src/
    app/
    components/
      ui/
      admin/
      storefront/
      assistant/
      checkout/
      orders/
    pages/
      admin/
      client/
    hooks/
    lib/
      api/
      query/
    types/
    assets/
    styles/
```

```text
backend/
  app/
    main.py
    api/
      routes/
    core/
    db/
    models/
    schemas/
    services/
      catalog.py
      cart.py
      quote.py
      policy.py
      orders.py
      payments.py
    agents/
      commerce_agent.py
      external_buyer.py
    mcp/
      server.py
      tools.py
    integrations/
      razorpay.py
      openai.py
    audit/
```

## Backend

- Pydantic schemas for request/response validation.
- SQLAlchemy models never leak directly into API responses.
- Services contain business logic.
- Routes are thin.
- Dependency injection is used for DB/session/config where useful.
- Use transactions for state changes.
- Never trust frontend totals.
- Validate ownership of carts/orders.
- Validate product active status.
- Validate inventory before cart mutation and again during final quote.
- Use integer paise for INR monetary values.

## API Response Pattern

Use predictable responses:

```json
{
  "success": true,
  "data": {}
}
```

Errors:

```json
{
  "success": false,
  "error": {
    "code": "PRODUCT_OUT_OF_STOCK",
    "message": "This product is currently out of stock."
  }
}
```

Never expose stack traces or secrets.

## Agent Rules

- Agent may reason and choose tools.
- Agent cannot invent price or inventory.
- Agent cannot mark payment successful.
- Agent cannot bypass purchase approval.
- Agent tool calls must invoke commerce services.
- Log critical tool calls to audit events.
- Handle model/API failures gracefully.

## Security

- Never send Razorpay key secret to frontend.
- Never store secrets in git.
- Never trust client-supplied amount.
- Verify payment signatures server-side.
- Verify webhook signatures.
- Make payment event handling idempotent.
- Sanitize and validate all external input.

## Naming

- Python files: snake_case.
- Python functions/variables: snake_case.
- React component files: PascalCase.
- TypeScript utility files: camelCase.
- Route paths: kebab-case.
- Database tables: snake_case plural.

## UI

- Follow `ui-rules.md` and `ui-tokens.md`.
- No arbitrary colors.
- No giant component files.
- No inline styles unless required for a computed visual value.
