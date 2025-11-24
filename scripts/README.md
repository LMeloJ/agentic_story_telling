# Utility Scripts

This directory contains utility scripts for managing the ChromaDB memory database.

## Scripts

### `load_sample_memories.py`

Load sample memories into ChromaDB for testing and visualization.

**Usage:**
```bash
# Load sample memories (keeps existing memories)
uv run python scripts/load_sample_memories.py

# Clear existing memories and load fresh samples
uv run python scripts/load_sample_memories.py --clear
```

**What it does:**
- Creates 17 diverse sample memories across 3 NPCs (alice, bob, charlie)
- Includes memories with different:
  - Importance scores (0.2 to 1.0)
  - Memory types (conversation, relationship, event)
  - Timestamps (recent to 7 days ago)
  - Tags and content themes
- Perfect for testing the visualization notebook

**Sample NPCs:**
- **alice**: Scholar/researcher with quest-related memories
- **bob**: Trader/friend with relationship and helpful memories
- **charlie**: Former guard with secrets and personal memories

### `reset_memory_database.py`

Reset/clear the ChromaDB memory database.

**Usage:**
```bash
# Reset all collections (with confirmation)
uv run python scripts/reset_memory_database.py

# Reset all collections (skip confirmation)
uv run python scripts/reset_memory_database.py --yes

# Reset specific collections
uv run python scripts/reset_memory_database.py --collections npc_memories world_knowledge
```

**What it does:**
- Shows current database state
- Prompts for confirmation (unless `--yes` flag is used)
- Deletes all memories from specified collections
- Verifies the reset completed successfully

**Collections:**
- `npc_memories` - NPC conversation memories
- `world_knowledge` - Shared world context
- `character_profiles` - NPC personality embeddings
- `relationship_graph` - NPC-to-NPC relationships

## Workflow for Testing

1. **Reset the database** (start fresh):
   ```bash
   uv run python scripts/reset_memory_database.py --yes
   ```

2. **Load sample memories**:
   ```bash
   uv run python scripts/load_sample_memories.py --clear
   ```

3. **Visualize in notebook**:
   ```bash
   uv run jupyter notebook
   ```
   Then open `notebooks/visualize_memory_embeddings.ipynb`

4. **Repeat as needed** for testing different scenarios!

## Tips

- Use `--clear` when loading samples to start with a clean dataset
- Use `--yes` flag when resetting to skip confirmation (useful for automation)
- The scripts show detailed progress and final state
- Sample memories are designed to show diverse patterns for better visualization

