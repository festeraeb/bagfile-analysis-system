#!/usr/bin/env python3
"""
Setup script for BAG Processor with Rust acceleration using maturin
"""

from setuptools import setup

setup(
    name="bag-processor",
    version="0.1.0",
    packages=["bag_processor"],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.20.0",
        "rasterio>=1.2.0",
        "scipy>=1.7.0",
        "matplotlib>=3.3.0",
    ],
)