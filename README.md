# Ex-Ante Evaluation for Goal-Driven Prioritization of Redesigned Business Process Alternatives

This repository contains the prototypical instantiation of the reference architecture designed in my bachelor thesis, titled 'Choosing the Right Path: Ex-Ante Evaluation for Goal-Driven Prioritization of Redesigned Business Process Alternatives'.

This tool is designed to support process designers in evaluating redesigned business processes prior to implementation. By prioritizing alternatives based on individual context and goals, it provides systematic decision support regarding which alternative should be chosen and implemented.

<video controls width="100%">
<source src="https://github.com/LPSchirmer/bpr_evaluator/raw/refs/heads/master/demo_video.mp4">
</video>

---

## Requirements

Before you begin, ensure that the following software is installed on your system.

Note: If a command does not work as expected, try to replace "python" with "python3 or "pip" with "pip3".

1. Python

```bash
python --version
```

2. Pip (for dependency management and package handling)

```bash
pip --version
```

or

```bash
python -m pip --version
```

3. Git (to clone the repository)

```bash
git --version
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/LPSchirmer/bpr_evaluator
```

### 2. Navigate to the cloned directory and install all dependencies and packages

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

or

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

### 3. Credentials Setup

Rename the .env.example file to .env and add your Gemini API Key and Gemini model accordingly.
In general, any Gemini model can be used. However, this project was tested using Gemini 2.5 Flash.

---

## Running the System

```bash
.venv\Scripts\activate
streamlit run 1_Start_Evaluation.py
```

or

```bash
.venv\Scripts\activate
python -m streamlit run 1_Start_Evaluation.py
```

---

## Contact

For support, questions, or feedback regarding the repository, don't hesitate to contact me via E-Mail: [lucapaulschirmer@gmail.com](mailto:lucapaulschirmer@gmail.com)
