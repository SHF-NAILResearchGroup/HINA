from setuptools import setup, find_packages, Extension

__version__ = "0.6.8"

setup(
    name='hina',
    version=__version__,
    description='Heterogenous Interaction Network Analysis in Python',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://hina.readthedocs.io/en/latest/index.html',
    author='Shihui Feng, Baiyue He, Alec Kirkley',
    author_email='shihuife@hku.hk, baiyue.he@connect.hku.hk, akirkley@hku.hk',
    license='The MIT License',
    project_urls={
        "Documentation": "https://hina.readthedocs.io/en/latest/index.html",
        "Source": "https://hina.readthedocs.io/en/latest/index.html"
    },
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.24",    
        "pandas>=2.2",
        "scipy>=1.10",
        "python-multipart>=0.0.18",
        "dash<=3.0.0",
        "dash-cytoscape>=1.0.2",
        "matplotlib>=3.8.4",
        "networkx>=3.0",
        "fastapi>=0.111.0",
        "uvicorn>=0.30.0",
        "openpyxl>=3.1.5",
    ],
    extras_require={
        "dev": ["pytest", "pytest-cov", "pytest-html"],  
    },
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
)
