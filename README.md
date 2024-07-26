# Hymn PDF Generator

This project is used to generate PDFs for hymns. It uses the Python
programming language and the `poetry` package manager for dependency
management.

## Installation

1. Install Poetry: Poetry is a tool for dependency management and
packaging in Python. It allows you to declare the libraries your project
depends on and it will manage (install/update) them for you.

```bash
pip install poetry
```

2. Clone this repository:

```bash
git clone https://github.com/nitaibezerra/hymn_pdf_generator.git
```

3. Navigate to the project directory:

```bash
cd hymn_pdf_generator
```

4. Install the project dependencies:

```bash
poetry install
```

## Usage

1. Run the pdf_generator.py script under the poetry environment. Provide
the YAML file path as argument:

```bash
poetry run python hymn_pdf_generator/main.py example/selecao_aniversario_ingrid.yaml
```

The generated PDF will be created at the same place of the provided YAML.
In this case at `example/selecao_aniversario_ingrid.pdf`.