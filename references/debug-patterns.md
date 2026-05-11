# Debug Patterns — Living Knowledge Base
**Maintained by:** `agents/self-learn-engine.md`  
**Read by:** `agents/debug-agent.md` at session startup  
**Updated:** Automatically via Git commit after every new bug resolved  
**Format:** Each pattern block is auto-appended; never manually deleted

---

## How to Use This File

- The debug agent loads this file at startup and indexes it by `error_signal`
- If your bug signal matches, the agent applies the fix directly (no full diagnosis)
- Confidence rises with hit_count: `low → medium → high`
- High-confidence patterns (hit_count ≥ 10) are fast-pathed without re-diagnosis

---

## Pattern Index (auto-maintained)

| ID | Layer | Title | Confidence | Hits |
|----|-------|-------|-----------|------|
| DP-ABP-A3F1 | ABP | DI: service not registered in correct module | low | 1 |
| DP-ABP-B2C4 | ABP | Permission policy name mismatch (403) | low | 1 |
| DP-EFC-D1E2 | EF Core | Navigation property null — missing .Include() | low | 1 |
| DP-BLZ-F3A1 | Blazor | Component not re-rendering after async op | low | 1 |
| DP-BLZ-C2D4 | Blazor | JS Interop called too early (OnInitializedAsync) | low | 1 |
| DP-CSS-E4B3 | CSS | RTL layout broken — hardcoded left/right | low | 1 |
| DP-JS-G1H2 | JS | AJAX 400 — missing X-RequestVerificationToken | low | 1 |
| DP-JS-K3L1 | JS | abp.ui.block() not releasing — missing finally{} | low | 1 |
| DP-RZR-M2N4 | Razor | @Model null — OnGet() not populating property | low | 1 |
| DP-ADO-P1Q2 | ADO | Pipeline fails — secret variable not mapped to env | low | 1 |

---
### DP-ABP-A3F1 — DI: service not registered in correct module

| Field | Value |
|-------|-------|
| Layer | ABP |
| Error Signal | `cannot resolve service for type` |
| ABP Version | any |
| .NET Version | any |
| Confidence | low |
| Hit Count | 1 |
| First Seen | 2026-05-11 |
| Last Seen | 2026-05-11 |

**Root Cause:** Service is registered in a module that is not listed in `[DependsOn]` of the consuming module, so the DI container cannot resolve it.

**Fix:**
```csharp
// In the consuming AbpModule:
[DependsOn(
    typeof(YourServiceModule), // FIX: was missing — service lives in this module
    typeof(AnotherModule)
)]
public class YourAppModule : AbpModule { }
```

**Verification:**
1. `dotnet build` — no DI exception at startup
2. Hit the failing endpoint — returns 200

**Tags:** `di`, `module`, `dependson`, `abp`

---
### DP-ABP-B2C4 — Permission policy name mismatch (403)

| Field | Value |
|-------|-------|
| Layer | ABP |
| Error Signal | `authorizationexception` |
| ABP Version | any |
| .NET Version | any |
| Confidence | low |
| Hit Count | 1 |
| First Seen | 2026-05-11 |
| Last Seen | 2026-05-11 |

**Root Cause:** The string in `[Authorize(PolicyName = "...")]` does not exactly match the key defined in `PermissionDefinitionProvider`. Case-sensitive mismatch or copy-paste error.

**Fix:**
```csharp
// In PermissionDefinitionProvider:
public const string MyFeature = "MyApp.MyFeature"; // SOURCE OF TRUTH

// In AppService:
[Authorize(PolicyName = MyPermissions.MyFeature)] // FIX: use the constant, not a literal
public async Task<MyDto> GetAsync() { ... }
```

**Verification:**
1. Grep for the permission string — confirm single definition in `PermissionDefinitionProvider`
2. Grant permission to test user via permission management page
3. Call the endpoint — 200 returned

**Tags:** `permissions`, `authorize`, `403`, `abp`, `policy`

---
### DP-EFC-D1E2 — Navigation property null — missing .Include()

| Field | Value |
|-------|-------|
| Layer | EF Core |
| Error Signal | `navigation property is null` |
| ABP Version | any |
| .NET Version | any |
| Confidence | low |
| Hit Count | 1 |
| First Seen | 2026-05-11 |
| Last Seen | 2026-05-11 |

**Root Cause:** ABP disables lazy loading by default. Navigation properties are null unless explicitly `.Include()`d in the query.

**Fix:**
```csharp
// In repository or application service:
var order = await _orderRepository
    .GetQueryableAsync()
    .Include(o => o.OrderLines)    // FIX: lazy loading is OFF — must explicitly include
    .Include(o => o.Customer)      // FIX: add all required nav props
    .FirstOrDefaultAsync(o => o.Id == id);
```

**Verification:**
1. Add `.Include()` for all accessed nav props
2. Run query — nav props populated
3. No `NullReferenceException` in mapping

**Tags:** `efcore`, `include`, `navigation-property`, `lazy-loading`, `repository`

---
### DP-BLZ-F3A1 — Component not re-rendering after async operation

| Field | Value |
|-------|-------|
| Layer | Blazor |
| Error Signal | `component not updating ui` |
| ABP Version | any |
| .NET Version | any |
| Confidence | low |
| Hit Count | 1 |
| First Seen | 2026-05-11 |
| Last Seen | 2026-05-11 |

**Root Cause:** After an async operation completes, Blazor's render cycle is not triggered because `StateHasChanged()` was not called.

**Fix:**
```csharp
private async Task LoadDataAsync()
{
    _items = await _service.GetListAsync();
    StateHasChanged(); // FIX: trigger re-render after async completes
}

// Or with InvokeAsync for thread-safety (e.g., from a callback/event):
await InvokeAsync(StateHasChanged); // FIX: use when called from non-UI thread
```

**Verification:**
1. Data loads → UI updates immediately without manual page refresh
2. No double-render warnings in console

**Tags:** `blazor`, `statehaschanged`, `rendering`, `async`, `lifecycle`

---
### DP-BLZ-C2D4 — JS Interop called too early (OnInitializedAsync)

| Field | Value |
|-------|-------|
| Layer | Blazor |
| Error Signal | `javascript interop calls cannot be issued` |
| ABP Version | any |
| .NET Version | any |
| Confidence | low |
| Hit Count | 1 |
| First Seen | 2026-05-11 |
| Last Seen | 2026-05-11 |

**Root Cause:** `IJSRuntime.InvokeAsync` called during `OnInitializedAsync` before the DOM exists. JS Interop is only valid after the first render.

**Fix:**
```csharp
// WRONG — throws during prerender / OnInitializedAsync:
protected override async Task OnInitializedAsync()
{
    await JS.InvokeVoidAsync("myFunc"); // DOM not ready
}

// CORRECT — use OnAfterRenderAsync:
protected override async Task OnAfterRenderAsync(bool firstRender)
{
    if (firstRender)
    {
        await JS.InvokeVoidAsync("myFunc"); // FIX: DOM guaranteed ready here
    }
}
```

**Verification:**
1. No `JSException` on page load
2. JS function executes correctly after first render

**Tags:** `blazor`, `jsinterop`, `ijsruntime`, `onafterrenderasync`, `lifecycle`

---
### DP-CSS-E4B3 — RTL layout broken — hardcoded left/right

| Field | Value |
|-------|-------|
| Layer | CSS |
| Error Signal | `rtl layout misaligned` |
| ABP Version | any |
| .NET Version | any |
| Confidence | low |
| Hit Count | 1 |
| First Seen | 2026-05-11 |
| Last Seen | 2026-05-11 |

**Root Cause:** CSS uses physical `left`/`right` properties instead of logical `inline-start`/`inline-end`, breaking RTL (Arabic/Hebrew) layouts.

**Fix:**
```css
/* WRONG — breaks RTL */
.sidebar {
    margin-left: 16px;   /* hardcoded physical direction */
    text-align: left;    /* doesn't flip in RTL */
}

/* FIX: use logical properties */
.sidebar {
    margin-inline-start: 16px;  /* FIX: flips automatically in RTL */
    text-align: start;          /* FIX: RTL/LTR neutral */
}
```

**Verification:**
1. Add `dir="rtl"` to `<html>` — layout mirrors correctly
2. Remove `dir="rtl"` — layout returns to LTR correctly
3. Syncfusion components align icons and text correctly in both directions

**Tags:** `css`, `rtl`, `arabic`, `logical-properties`, `syncfusion`, `gcc`

---
### DP-JS-G1H2 — AJAX 400 — missing X-RequestVerificationToken

| Field | Value |
|-------|-------|
| Layer | JavaScript |
| Error Signal | `400 bad request ajax` |
| ABP Version | any |
| .NET Version | any |
| Confidence | low |
| Hit Count | 1 |
| First Seen | 2026-05-11 |
| Last Seen | 2026-05-11 |

**Root Cause:** ASP.NET Core anti-forgery middleware rejects the AJAX POST because the `X-RequestVerificationToken` header is missing.

**Fix:**
```javascript
const token = document.querySelector('input[name="__RequestVerificationToken"]').value;

fetch('/api/my-endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-RequestVerificationToken': token  // FIX: anti-forgery header
    },
    body: JSON.stringify(payload)
});
```

**Verification:**
1. Network tab → request has `X-RequestVerificationToken` header
2. Response is 200, not 400

**Tags:** `javascript`, `ajax`, `antiforgery`, `400`, `token`, `abp`

---
### DP-JS-K3L1 — abp.ui.block() not releasing — missing finally{}

| Field | Value |
|-------|-------|
| Layer | JavaScript |
| Error Signal | `page blocked ui not unblocking` |
| ABP Version | any |
| .NET Version | any |
| Confidence | low |
| Hit Count | 1 |
| First Seen | 2026-05-11 |
| Last Seen | 2026-05-11 |

**Root Cause:** `abp.ui.block()` is called but an exception thrown before `abp.ui.unblock()` runs, leaving the page permanently blocked.

**Fix:**
```javascript
abp.ui.block();
try {
    const result = await riskyCall(); // FIX: any exception is caught
    processResult(result);
} catch (err) {
    abp.notify.error(err.message || 'An error occurred');
} finally {
    abp.ui.unblock(); // FIX: always runs, even on error
}
```

**Verification:**
1. Trigger an error in the operation — page unblocks automatically
2. Spinner/overlay disappears after both success and failure paths

**Tags:** `javascript`, `abp-ui`, `block`, `unblock`, `finally`, `loading`

---
### DP-RZR-M2N4 — @Model null — OnGet() not populating property

| Field | Value |
|-------|-------|
| Layer | Razor |
| Error Signal | `object reference not set model null` |
| ABP Version | any |
| .NET Version | any |
| Confidence | low |
| Hit Count | 1 |
| First Seen | 2026-05-11 |
| Last Seen | 2026-05-11 |

**Root Cause:** The Razor PageModel property used as `@Model.X` is never populated in `OnGet()` / `OnGetAsync()`, so it's null at render time.

**Fix:**
```csharp
public class MyPageModel : AbpPageModel
{
    public MyDto MyData { get; set; }

    public async Task OnGetAsync(Guid id)
    {
        MyData = await _service.GetAsync(id);  // FIX: populate before return Page()
    }
}
```

**Verification:**
1. Page renders without `NullReferenceException`
2. `@Model.MyData.SomeField` displays expected value

**Tags:** `razor`, `pagemodel`, `onget`, `null`, `abp`, `model`

---
### DP-ADO-P1Q2 — Pipeline fails — secret variable not mapped to env

| Field | Value |
|-------|-------|
| Layer | ADO |
| Error Signal | `environment variable not found pipeline` |
| ABP Version | any |
| .NET Version | any |
| Confidence | low |
| Hit Count | 1 |
| First Seen | 2026-05-11 |
| Last Seen | 2026-05-11 |

**Root Cause:** A secret variable defined in the variable group is not explicitly mapped to an environment variable in the YAML pipeline step.

**Fix:**
```yaml
- task: DotNetCoreCLI@2
  inputs:
    command: 'publish'
  env:
    MY_SECRET: $(MY_SECRET)       # FIX: map variable group secret to step env
    CONNECTION_STRING: $(ConnectionString)  # FIX: same for other secrets
```

**Verification:**
1. Pipeline run → step exits 0
2. Application reads the env var correctly at runtime

**Tags:** `ado`, `pipeline`, `secrets`, `variable-group`, `yaml`, `env`

---

<!-- END OF PATTERNS — self-learn-engine appends below this line -->
