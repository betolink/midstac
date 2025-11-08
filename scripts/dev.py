#!/usr/bin/env python3
import subprocess

cmd = ["mcpo", "--hot-reload", "--cors-allow-origins", "*", "--port", "8000", "--", "midstac"]

subprocess.run(cmd)
