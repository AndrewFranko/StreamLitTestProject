# Test LangChain Long-Term Store (SqliteStore)

**Purpose**: Verify that long-term memory actually persists to database when langgraph is installed

---

## Step 1: Install langgraph

```bash
pip install langgraph
```

Verify installation:
```bash
python -c "import langgraph; print('langgraph installed:', langgraph.__version__)"
```

---

## Step 2: Run the test

```bash
cd c:/StreamLit
python << 'EOF'
import sys
sys.path.insert(0, 'src')
import os
from agent_engine import AgentEngine

print("=" * 70)
print("TESTING LANGGRAPH SQLITESTORE")
print("=" * 70)

# Clean up old databases
for role in ['operator', 'engineer']:
    db_path = f'data/memory/long_term_memory_{role}.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted: {db_path}")

print("\n[1] Creating agent 1 (operator)...")
agent1 = AgentEngine('operator')
print(f"    Store active: {agent1.store is not None}")
print(f"    Database path: data/memory/long_term_memory_operator.db")

print("\n[2] Storing memory in agent 1...")
result = agent1.store_memory(
    key='machine_maintenance_pattern',
    value='MX-204 maintenance window: 6 AM before shift. High temperature in afternoons.',
    tags=['machine', 'MX-204', 'pattern']
)
print(f"    Store result: {result}")

print("\n[3] Retrieving from agent 1 (same instance)...")
retrieved = agent1.retrieve_memory('machine_maintenance_pattern')
print(f"    Retrieved: {retrieved[:50]}..." if retrieved else "    Retrieved: None")

print("\n[4] Creating agent 2 (NEW instance, same role)...")
agent2 = AgentEngine('operator')

print("\n[5] Retrieving from agent 2 (different instance, same role)...")
retrieved = agent2.retrieve_memory('machine_maintenance_pattern')
if retrieved:
    print(f"    ✅ SUCCESS: Retrieved from database!")
    print(f"    Value: {retrieved[:50]}...")
else:
    print(f"    ❌ FAILED: Retrieved None (langgraph may not be working)")

print("\n[6] Checking database file exists...")
db_path = 'data/memory/long_term_memory_operator.db'
if os.path.exists(db_path):
    size = os.path.getsize(db_path)
    print(f"    ✅ Database file exists: {db_path}")
    print(f"    Size: {size} bytes")
else:
    print(f"    ❌ Database file NOT found: {db_path}")

print("\n[7] Testing engineer isolation...")
engineer = AgentEngine('engineer')
eng_result = engineer.retrieve_memory('machine_maintenance_pattern')
if eng_result is None:
    print(f"    ✅ Engineer cannot see operator's data (isolation works)")
else:
    print(f"    ❌ Engineer retrieved operator's data (isolation broken)")

print("\n[8] Storing engineer data...")
engineer.store_memory(
    key='e17_diagnostic',
    value='E17 error: check pump seal pressure gauge',
    tags=['E17', 'diagnostic']
)

print("\n[9] Verify engineer data in new instance...")
engineer2 = AgentEngine('engineer')
eng_data = engineer2.retrieve_memory('e17_diagnostic')
if eng_data:
    print(f"    ✅ Engineer's memory persisted across instances")
    print(f"    Value: {eng_data[:40]}...")
else:
    print(f"    ❌ Engineer's memory NOT persisted")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
EOF
```

---

## Step 3: Expected Output

### If langgraph IS installed ✅

```
======================================================================
TESTING LANGGRAPH SQLITESTORE
======================================================================

[1] Creating agent 1 (operator)...
    Store active: True
    Database path: data/memory/long_term_memory_operator.db

[2] Storing memory in agent 1...
    Store result: True

[3] Retrieving from agent 1 (same instance)...
    Retrieved: MX-204 maintenance window: 6 AM before shift...

[4] Creating agent 2 (NEW instance, same role)...

[5] Retrieving from agent 2 (different instance, same role)...
    ✅ SUCCESS: Retrieved from database!
    Value: MX-204 maintenance window: 6 AM before shift...

[6] Checking database file exists...
    ✅ Database file exists: data/memory/long_term_memory_operator.db
    Size: 8192 bytes

[7] Testing engineer isolation...
    ✅ Engineer cannot see operator's data (isolation works)

[8] Storing engineer data...

[9] Verify engineer data in new instance...
    ✅ Engineer's memory persisted across instances
    Value: E17 error: check pump seal pressure gauge...

======================================================================
TEST COMPLETE
======================================================================
```

### If langgraph NOT installed ❌

```
[1] Creating agent 1 (operator)...
    Store active: False  # ← Will be None without langgraph
    
[5] Retrieving from agent 2...
    ❌ FAILED: Retrieved None (langgraph may not be working)

[6] Checking database file exists...
    ❌ Database file NOT found
```

---

## Step 4: Verify Database Files

```bash
# List database files created
ls -lah c:/StreamLit/data/memory/

# Output should show:
# long_term_memory_operator.db
# long_term_memory_engineer.db
# long_term_memory_supervisor.db
# long_term_memory_plant_manager.db
```

---

## Step 5: Inspect Database Contents (Optional)

```bash
# Install sqlite3 CLI (already available on most systems)
sqlite3 c:/StreamLit/data/memory/long_term_memory_operator.db ".tables"
sqlite3 c:/StreamLit/data/memory/long_term_memory_operator.db ".schema"
sqlite3 c:/StreamLit/data/memory/long_term_memory_operator.db "SELECT * FROM items LIMIT 5;"
```

---

## What This Test Proves

✅ **Langgraph SqliteStore Working**
- Memory stored to database
- Persists across agent instances
- Data survives session restarts

✅ **Role Isolation at DB Level**
- Operator's data in `long_term_memory_operator.db`
- Engineer's data in `long_term_memory_engineer.db`
- Engineer cannot retrieve operator's stored memory

✅ **Database Files Created**
- 4 separate `.db` files per role
- Each contains that role's memories only

---

## Troubleshooting

### Error: "langgraph not available"
```
Solution: pip install langgraph
```

### Database file not created
```
Solution: Check data/memory/ directory exists
          mkdir -p c:/StreamLit/data/memory/
```

### Retrieved returns None even with langgraph
```
Solution: Make sure you're using same role for agent1 and agent2
          agent1 = AgentEngine('operator')  # Stores here
          agent2 = AgentEngine('operator')  # Retrieves from same role DB
```

### Store result is False
```
Solution: Likely langgraph not installed
          pip install langgraph
          Restart Python interpreter
```

---

## Next: Test in Streamlit

Once you confirm SqliteStore works in Python:

```bash
streamlit run app.py
```

Then in the UI:
1. Select "Operator" role
2. Ask question (builds session memory)
3. Close browser / Restart app
4. Select "Operator" again
5. ✅ Session memory empty (new session)
6. But any data stored via `store_memory()` persists in long-term DB

---

## Summary

| Component | Without langgraph | With langgraph |
|-----------|-------------------|-----------------|
| Session Memory | ✅ Works (50 messages) | ✅ Works |
| Long-Term Store | ❌ Returns None | ✅ Persists to DB |
| Database Files | ❌ Not created | ✅ Created per role |
| Role Isolation | ✅ Code-level | ✅ DB-level |
| Persistence | ❌ Lost on restart | ✅ Survives restart |

**Status**: Run the test above to verify langgraph SqliteStore is working!
