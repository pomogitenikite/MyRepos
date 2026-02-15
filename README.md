# smart_clicker

Windows-only recorder/player for UI automation scenarios on `pywinauto==0.6.8`.

## Install

```bash
pip install -e .
```

## Usage

Record:

```bash
smart-clicker record --out scenario.yaml --name demo
```

Play all runs:

```bash
smart-clicker play scenario.yaml
```

Play one run:

```bash
smart-clicker play scenario.yaml --run run_001
```
