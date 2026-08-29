# DNA Metaphors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Weave four approved DNA-metaphor touches into the Genom landing page copy with zero loss of meaning.

**Architecture:** One task, four exact string replacements in index.html text nodes. Nothing else changes anywhere.

**Tech Stack:** Plain text edit. Verification: grep, `python3 -m unittest`, browser check by the coordinator.

**Spec:** `docs/superpowers/specs/2026-08-29-dna-metaphors-design.md` (the four pairs are user-approved verbatim).

## Global Constraints

- Exactly the four listed replacements; every other byte of the repo untouched (including meta description, console.html, JS, server.py).
- The keccak256 formula text stays verbatim inside touch 3.
- Commit message ends with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Four DNA touches in index.html

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Apply the four replacements** (old ⇒ new, text nodes only)

1. `$GENOM — A SELF-DRIVING INDEX TOKEN, BOXED IN BY HARD LIMITS` ⇒ `$GENOM — A SELF-DRIVING INDEX TOKEN WITH HARD LIMITS WRITTEN INTO ITS DNA`
2. `The weights are chosen by an autonomous agent.` ⇒ `The weights — the basket's genome — are chosen by an autonomous agent.`
3. `Before a single asset moves, the agent publishes keccak256(epoch, weights, thesis, nonce).` ⇒ `Before a single asset moves, the agent publishes keccak256(epoch, weights, thesis, nonce) — the decision's full genetic sequence.`
4. `A vector that fails any check is voided…` — exact old sentence: `If any check fails, the epoch is voided and the basket does not move.` ⇒ `A vector that fails any check is a mutation that never replicates: the epoch is voided and the basket does not move.`

- [ ] **Step 2: Verify**

`git diff --stat` shows ONLY `index.html` with 4 changed regions; `grep -c "genetic sequence\|basket's genome\|INTO ITS DNA\|mutation that never replicates" index.html` → 4 total (one each). `python3 -m unittest tests.test_server -q` → 46 OK (safety run).

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "copy: weave four DNA metaphors into the landing (meaning preserved)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
