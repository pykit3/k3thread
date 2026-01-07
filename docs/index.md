# k3thread

[![Action-CI](https://github.com/pykit3/k3thread/actions/workflows/python-package.yml/badge.svg)](https://github.com/pykit3/k3thread/actions/workflows/python-package.yml)
[![Documentation Status](https://readthedocs.org/projects/k3thread/badge/?version=stable)](https://k3thread.readthedocs.io/en/stable/?badge=stable)
[![Package](https://img.shields.io/pypi/pyversions/k3thread)](https://pypi.org/project/k3thread)

Thread utilities for daemon threads and exception sending.

k3thread is a component of [pykit3](https://github.com/pykit3) project: a python3 toolkit set.

## Installation

```bash
pip install k3thread
```

## Quick Start

```python
import k3thread
import time

# Start a daemon thread after delay
th = k3thread.daemon(lambda: print("hello"), after=0.2)

# Start a daemon thread with a function
def worker():
    while True:
        time.sleep(0.1)

t = k3thread.daemon(worker)

# Stop a thread by sending an exception
k3thread.send_exception(t, SystemExit)
```

## API Reference

::: k3thread

## License

The MIT License (MIT) - Copyright (c) 2015 Zhang Yanpo (张炎泼)
