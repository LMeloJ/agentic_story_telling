# Notebooks

This directory contains Jupyter notebooks for visualization and analysis of the Dynevi memory system.

## Memory Embedding Visualization

**File**: `visualize_memory_embeddings.ipynb`

A comprehensive visualization tool for exploring memory embeddings stored in ChromaDB using t-SNE (t-Distributed Stochastic Neighbor Embedding).

### Features

- **2D Embedding Visualization**: Uses t-SNE to reduce high-dimensional embeddings to 2D for visualization
- **Multiple Color Schemes**: 
  - Color by NPC ID
  - Color by memory type
  - Color by importance score
- **Interactive Visualization**: Optional Plotly integration for interactive exploration
- **Cluster Analysis**: K-means clustering to identify memory groups
- **Similarity Analysis**: Find nearest neighbors for any memory
- **Statistical Summary**: Comprehensive statistics about your memories

### Usage

1. **Install Dependencies** (if not already installed):
   ```bash
   uv sync --group dev
   ```

2. **Optional: Install Plotly for Interactive Visualizations**:
   ```bash
   uv pip install plotly
   ```

3. **Start Jupyter Notebook**:
   ```bash
   uv run jupyter notebook
   ```

4. **Open the Notebook**:
   - Navigate to `notebooks/visualize_memory_embeddings.ipynb`
   - Run all cells to generate visualizations

### Prerequisites

- ChromaDB must be initialized with some memories stored
- The notebook will automatically load your ChromaDB data from `./data/chroma_db`
- By default, it visualizes the `npc_memories` collection, but you can change this in the notebook

### What You'll See

- **Memory Distribution**: See how memories are distributed in embedding space
- **NPC Clusters**: Identify if memories from different NPCs form distinct clusters
- **Memory Similarity**: Visualize which memories are semantically similar
- **Importance Patterns**: See if high-importance memories cluster together
- **Memory Types**: Explore how different memory types (conversation, event, relationship) are distributed

### Tips

- Adjust `perplexity` and `n_iter` in the t-SNE cell if you have a very large or very small dataset
- Modify `n_clusters` in the clustering cell based on your data size
- Change `memory_idx` in the nearest neighbors cell to explore different memories
- The notebook saves visualization data to `data/memory_visualization_data.csv` for further analysis

### Troubleshooting

- **"No memories found"**: Make sure you have stored some memories in ChromaDB first
- **t-SNE takes too long**: Reduce `n_iter` or sample a subset of your data
- **Plotly not working**: Install with `uv pip install plotly` or use the matplotlib fallback

