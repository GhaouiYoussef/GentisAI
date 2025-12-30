# GentisAI

<div align="center">
    <picture>
      <source media="(prefers-color-scheme: light)" srcset="assets/images/GentisAI-B-banner-r.svg">
      <source media="(prefers-color-scheme: dark)" srcset="assets/images/GentisAI-B-banner-r.svg">
      <img alt="GentisAI-B-banner-r" src="assets/images/GentisAI-B-banner-r.svg" width="80%">
    </picture>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" />
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" />
  <img src="https://img.shields.io/badge/status-beta-orange" />
</p>

<h3 align="center"><i>The lightweight framework for real-time AI agents.</i></h3>

<p align="center">
  Build multi-expert systems with precise routing, zero overhead, and
  <b>6× less token usage than major competitors</b>.
</p>

---

## Why GentisAI?

Traditional agent frameworks (LangChain, CrewAI, AutoGen…) are created for **complex, autonomous, long-running tasks**.
They introduce:

* Heavy orchestration layers
* Hidden “manager” reasoning loops
* Massive prompts
* Slow response times
* High token usage

**GentisAI is built for a different purpose:**

👉 **Create fast, deterministic, conversational AI agents that feel real-time.**

---

## 🔥 The Gentis Advantage

### ⚡ **6× More Efficient**

Our architecture uses **~83% fewer tokens per turn** than CrewAI in benchmarks.

### 🎯 **Precise Expert Routing**

A tiny, dedicated router sends each message to the correct expert
— fast, deterministic, and with no “agent arguing with itself.”

### 🪶 **Minimalist API**

Experts are simple Python classes.
Router is a single object.
Flow is one line.

### 🔍 **Fully Transparent**

No black-box loops.
You control the routing logic, prompts, and state.

### 🛠️ **Production-Ready Structure**

Clean separation of concerns:

* Experts
* Router
* Flow
* Memory
* LLM Adapters
