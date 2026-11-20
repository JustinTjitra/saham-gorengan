# <ID>: <title>

- **Phase:** <P0..P6>
- **Model:** sonnet | haiku
- **Deps:** <ids or none>
- **Size:** ~<n> lines

## Goal
One or two sentences: what exists after this chunk that did not before, and why it matters.

## Files
Exact paths the coder may create or modify. Nothing else.
- `src/saham_gorengan/<module>.py` (new)
- `tests/test_<module>.py` (new)

## Interface
Exact signatures with types and a docstring sentence each.
```python
def example(df: pd.DataFrame, window: int = 20) -> pd.Series: ...
```

## Behaviour
Bullet rules, edge cases, and what to do with bad input (raise which error, or skip and log).

## Acceptance
Tests that must exist and pass. Concrete inputs and expected outputs.
- `test_...`: given ..., returns ...

## Out of scope
What not to do in this chunk, even if it seems helpful.

## References
Research notes or PLAN.md sections the coder can read for context.
