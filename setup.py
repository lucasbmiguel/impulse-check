from setuptools import setup, find_packages

setup(
    name="impulse-check",
    version="1.1.0",
    py_modules=["main"],
    install_requires=[
        "windows-curses;platform_system=='Windows'",
    ],
    entry_points={
        "console_scripts": [
            "impulse-check=main:cli",
        ],
    },
    author="Lucas Bonatto",
    author_email="lucas.bonatto@example.com",
    description="A TUI app to track impulses and build better habits",
    keywords="habit-tracker, impulse-control, cli",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console :: Curses",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Utilities",
    ],
)