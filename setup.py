from setuptools import setup, find_packages


base_packages = [
    "fastapi",  # ==0.87.0
    "Jinja2",  # ==3.1.2
    "pandas",  # ==1.5.2
    "pydantic",  # ==1.10.2
    "requests",  # ==2.28.1
    "socketIO-client",  # ==0.7.2
    "uvicorn",  # ==0.20.0
]

dev_packages = ["jupyterlab", "mypy", "flake8", "black"]


setup(
    name="volco",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=base_packages,
    description="",
    extras_require={"dev": dev_packages},
    author="Ondrej Zacha",
    long_description_content_type="text/markdown",
    entry_points={"console_scripts": [
        "refresh = volco.volumio_scraper:main",
    ]},
)
