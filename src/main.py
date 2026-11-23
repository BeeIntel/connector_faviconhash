#!/usr/bin/env python3
import sys
import time
from favicon_hash import FaviconHashConnector

if __name__ == "__main__":
    try:
        connector = FaviconHashConnector()
        connector.start()
    except Exception as e:
        print(e)
        time.sleep(10)
        sys.exit(0)