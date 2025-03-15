# Impulse Check

A TUI (Text User Interface) application to track impulses and build better habits.

## Features

- Create and manage multiple habit/impulse tracking goals
- Simple counter interface for each goal
- Undo functionality for accidental counts
- User-friendly TUI with keyboard navigation

## Installation

### Using pip (Recommended)

```bash
pip install git+https://github.com/lucasbmiguel/impulse-check.git
```

### From source

```bash
git clone https://github.com/lucasbmiguel/impulse-check.git
cd impulse-check
pip install -e .
```

### Standalone executable

Download the latest release for your platform from the [Releases page](https://github.com/lucasbmiguel/impulse-check/releases).

## Usage

After installation, simply run:

```bash
impulse-check
```

To see the version:

```bash
impulse-check --version
```

## Navigation

- **Menu screen**:
  - `↑`/`↓`: Navigate goals
  - `Enter`: Open selected goal
  - `C`: Create new goal
  - `D`: Delete selected goal
  - `Q`: Quit application

- **Goal screen**:
  - `I`: Increment counter
  - `U`: Undo last increment
  - `M`: Return to menu
  - `Q`: Quit application

## License

MIT
