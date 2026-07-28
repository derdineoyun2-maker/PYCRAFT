# ⚡ 2D Python Redstone Engine (Beta 1.0)

A lightweight, standalone 2D Redstone Logic Simulator written in Python using Pygame. Designed with modularity in mind so developers can easily fork and contribute new blocks, logic, or features.

## 🚀 Features
- **Paginating Chest GUI:** 27 slots per page with interactive `<` and `>` button navigation.
- **Advanced Mechanics:** Repeaters (delays), Comparators, Pistons, Observers, and Sculk Sensors (wireless vibrations).
- **Procedural Pixel Art:** Zero external `.png` dependencies. Fully rendered using Python algorithms.
- **Developer Friendly:** Clean Object-Oriented Architecture (`RedstoneEngine` class).

## 🎮 Controls
- **Left Click:** Break Block
- **Right Click:** Place Block / Toggle Component (Switch, Repeater Tick, Comparator Mode)
- **Middle Click:** Pick Block from Grid
- **[E]:** Open/Close Inventory GUI
- **[R]:** Clear Grid Map
- **[1-9]:** Fast Hotbar Selection

## 🛠️ How to Contribute / Add New Blocks
1. Add your block definition to `ALL_TOOLS` dictionary.
2. Implement your visual texture logic inside `draw_texture()`.
3. Add custom propagation rules in `update_signals()`.
4. Submit a Pull Request!

## 📦 Installation
```bash
pip install pygame
python main.py
