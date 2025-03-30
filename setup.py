from setuptools import setup, find_packages

setup(
    name="catan",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytest>=7.4.3",
        "pytest-cov>=4.1.0",
    ],
    python_requires=">=3.9",
    author="Mihajlo Pavlovic",
    description="A Catan board game implementation",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
    ],
) 