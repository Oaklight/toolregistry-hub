# Agentic Sandbox / VM Solutions Research

**Date:** 2026-03-25
**Purpose:** Survey existing sandbox and VM solutions for running code safely in AI agent contexts, with an eye toward potential integration with toolregistry-hub.

---

## 1. Executive Summary

The AI agent sandbox market has matured rapidly through 2025-2026. The core problem is well-defined: AI agents generate and execute arbitrary code, and that code must be isolated from the host system, other tenants, and sensitive resources.

Solutions span a wide spectrum of isolation technologies:

| Isolation Level | Technology | Startup Speed | Security | Examples |
|---|---|---|---|---|
| **Kernel-level** | Landlock LSM, Seatbelt | Instant | Medium | nono |
| **Container** | Docker, OCI containers | ~1-5s | Medium | Docker Sandboxes, SWE-ReX |
| **Container + kernel sandbox** | gVisor (runsc) | Sub-second | Medium-High | Modal Sandboxes, Cloudflare Sandbox SDK |
| **microVM** | Firecracker, Cloud Hypervisor | ~0.5-3s | High | E2B, BoxLite, Fly.io Sprites, Gondolin |
| **microVM + Kata** | Kata Containers | ~1-3s | High | Kubernetes Agent Sandbox, Northflank |
| **Full VM** | QEMU, Apple Virtualization | ~5-30s | Very High | CUA (trycua) |

**Key market dynamics:**
- **Daytona** (70k+ stars) dominates mindshare as a general-purpose AI code execution platform with SDK-first design.
- **E2B** (~11k stars) pioneered the Firecracker-based ephemeral sandbox model and remains the de facto standard for API-driven agent sandboxing.
- **BoxLite** (~1.6k stars) positions itself as the "SQLite of sandboxes" -- embeddable, daemonless, local-first microVM isolation.
- **Modal** is the go-to for GPU workloads with gVisor-based sandboxes as part of a broader compute platform.
- **nono** (~1.2k stars) takes a unique kernel-enforcement approach (Landlock/Seatbelt) that is lightweight but narrower in scope.
- **Kubernetes Agent Sandbox** (k8s-sigs, ~1.5k stars) brings sandbox primitives to Kubernetes with pluggable backends (gVisor, Kata).
- **CUA** (~13k stars) focuses on computer-use agents with full desktop VM environments (macOS/Linux/Windows).

For toolregistry-hub, the most relevant options are those that provide **programmatic sandbox APIs** suitable for executing tool-generated code with minimal overhead. The top candidates are E2B, Daytona, Modal, BoxLite, and Docker Sandboxes, depending on deployment model (cloud vs. self-hosted vs. embedded).

---

## 2. Comparison Table

| Solution | Stars | Isolation | Language | Self-Hosted | Cloud Service | SDK Languages | Persistence | Startup | License | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| **Daytona** | 70,341 | Containers (Docker) | TypeScript | Yes | Yes | Python, TS, Go | Yes (lifecycle mgmt) | Sub-90ms (warm) | AGPL-3.0 | Very Active |
| **CUA (trycua)** | 13,256 | Full VM (Apple Virt, QEMU) | Python | Yes | Yes (cloud provider) | Python | Yes | 5-30s | MIT | Very Active |
| **E2B** | 11,422 | Firecracker microVM | Python | Yes (self-host infra) | Yes | Python, TS, Go | No (ephemeral, max 24h) | ~1-2s | Apache-2.0 | Very Active |
| **BoxLite** | 1,611 | microVM (KVM, no daemon) | Rust | Yes (embeddable) | No (local-first) | Python, TS, Rust | Yes (snapshots) | Sub-second | Apache-2.0 | Active |
| **K8s Agent Sandbox** | 1,480 | gVisor / Kata (pluggable) | Go | Yes (K8s cluster) | No | Python, kubectl | Yes (PVC) | ~2-5s | Apache-2.0 | Active |
| **nono** | 1,237 | Kernel (Landlock/Seatbelt) | Rust | Yes (local) | No | Python, Rust, CLI | N/A (process sandbox) | Instant | Apache-2.0 | Active |
| **Gondolin** | 809 | Firecracker microVM | TypeScript | Yes | No | TypeScript | No | ~1s | Apache-2.0 | Active |
| **SWE-ReX** | 454 | Docker containers | Python | Yes | Yes (AWS Fargate, Modal) | Python | No (ephemeral) | ~2-5s | MIT | Active |
| **Modal Sandboxes** | 451 (client) | gVisor | Python | No (cloud only) | Yes | Python, TS, Go | FS + Memory | Sub-second | Apache-2.0 | Active |
| **EdgeBox** | 199 | Firecracker (E2B fork) | TypeScript | Yes (local) | No | TypeScript | Yes | ~1-2s | GPL-3.0 | Active |
| **OpenKruise Agents** | 130 | Kubernetes pods | Go | Yes (K8s cluster) | No | Go, kubectl | Yes | ~2-5s | Apache-2.0 | Active |
| **CodeSandbox SDK** | 102 | Firecracker microVM | TypeScript | No (cloud only) | Yes | TypeScript | Yes (snapshots) | ~2s | Proprietary | Active |
| **Docker Sandboxes** | N/A | Container + microVM | Go | Yes (Docker Desktop) | No | CLI | Yes (workspace) | ~1-3s | Proprietary | Experimental |
| **Fly.io Sprites** | N/A | Firecracker microVM | Go | No (cloud only) | Yes | Go, TS, CLI | Yes (persistent) | ~1s | Proprietary | Active |
| **Runloop** | N/A | microVM | N/A | No (cloud only) | Yes | Python, TS | Yes (snapshots) | N/A | Proprietary | Active |
| **Together Code Sandbox** | N/A | VM | N/A | No (cloud only) | Yes | TS (CSB SDK) | FS + Memory | 0.5s (resume) | Proprietary | Active |
| **Blaxel** | N/A | microVM | N/A | No (cloud only) | Yes | Python, TS | Yes (perpetual) | ~25ms (resume) | Proprietary | Active |
| **Cloudflare Sandbox SDK** | N/A | Containers (CF Containers) | TypeScript | No (cloud only) | Yes | TypeScript | No (ephemeral) | Instant | Proprietary | Active |
| **Northflank Sandboxes** | N/A | Kata/Firecracker/gVisor | N/A | Yes (BYOC) | Yes | API | Yes | ~1s | Proprietary | Active |

---

## 3. Detailed Analysis

### 3.1 Daytona

- **Repository:** https://github.com/daytonaio/daytona
- **Stars:** 70,341
- **Description:** "Secure and Elastic Infrastructure for Running AI-Generated Code." Originally a development environment manager, pivoted to AI sandbox infrastructure.
- **Architecture:** SDK-managed sandbox lifecycle on top of Docker containers. Workspaces provide isolated environments with lifecycle automation (auto-stop, auto-archive, auto-delete). Container-level isolation, not microVM.
- **Language/Runtime:** TypeScript (platform); Python, TS, Go SDKs
- **Key Features:**
    - Sub-90ms warm start
    - Snapshot and restore
    - Lifecycle automation (idle timeouts, auto-archive)
    - Python, TypeScript, Go SDKs
    - Workspace concept with persistent storage
    - REST API for sandbox management
- **Pros:**
    - Largest community and mindshare
    - Very fast warm starts
    - Rich SDK ecosystem
    - Self-hostable with AGPL license
    - Well-documented
- **Cons:**
    - Container-level isolation (not hardware-level) -- less secure for truly untrusted code
    - AGPL-3.0 license has copyleft implications for commercial use
    - 4 vCPU, 8 GB RAM default cap per sandbox
- **License:** AGPL-3.0
- **Activity:** Very active, frequent releases, large contributor base

---

### 3.2 E2B

- **Repository:** https://github.com/e2b-dev/E2B (SDK), https://github.com/e2b-dev/infra (infrastructure)
- **Stars:** 11,422 (SDK), 980 (infra)
- **Description:** "Open-source, secure environment with real-world tools for enterprise-grade agents." Pioneered the ephemeral microVM sandbox model for AI agents.
- **Architecture:** Firecracker microVMs managed by a control plane (Nomad + Consul on GCP). Each sandbox is a full Linux VM with its own kernel. Custom templates built via Dockerfiles.
- **Language/Runtime:** Python (SDK), Go (infra)
- **Key Features:**
    - Firecracker microVM isolation (hardware-level)
    - Custom sandbox templates via Dockerfiles
    - Up to 8 vCPU, 8 GiB RAM per sandbox
    - Python and TypeScript SDKs
    - Desktop sandbox variant (with GUI)
    - MCP gateway for agent integration
    - Filesystem and process APIs
- **Pros:**
    - Strong hardware-level isolation
    - Clean, minimal SDK API
    - Well-established, widely adopted
    - Self-hostable infrastructure (open-source)
    - Desktop variant for computer-use agents
- **Cons:**
    - Ephemeral only (max 24h sessions)
    - No persistent state between sessions
    - Self-hosting requires running the full control plane (Nomad, Consul, Terraform)
    - Cloud pricing can add up at scale
- **License:** Apache-2.0
- **Activity:** Very active, core to many agent frameworks

---

### 3.3 BoxLite

- **Repository:** https://github.com/boxlite-ai/boxlite
- **Stars:** 1,611
- **Description:** "Sandboxes for every agent. Embeddable, stateful, snapshots, and hardware isolation." Positions itself as the "SQLite of sandboxes" -- daemonless, embeddable microVM.
- **Architecture:** KVM-based microVMs with no daemon requirement. Designed to be embedded directly into applications. Uses Linux KVM for hardware isolation without requiring a Firecracker-like VMM daemon.
- **Language/Runtime:** Rust (core), Python and TypeScript SDKs
- **Key Features:**
    - Embeddable -- no daemon or control plane needed
    - Hardware-level isolation via KVM
    - Stateful with snapshot/restore
    - Sub-second startup
    - Local-first design
    - MCP server integration (boxlite-mcp)
    - ClaudeBox integration for Claude Code
- **Pros:**
    - Truly embeddable (library, not service)
    - No infrastructure overhead
    - Hardware isolation without VM management complexity
    - Stateful snapshots
    - Local-first -- no cloud dependency
    - Apache-2.0 license
- **Cons:**
    - Requires Linux with KVM support
    - Relatively young project
    - Smaller community than E2B/Daytona
    - No managed cloud offering
    - Limited documentation compared to mature platforms
- **License:** Apache-2.0
- **Activity:** Active, growing community
- **Related Projects:**
    - `boxlite-mcp` -- MCP server for Claude Desktop integration
    - `boxrun` -- Ultra-lightweight sandbox platform powered by BoxLite

---

### 3.4 CUA (Computer Use Agents)

- **Repository:** https://github.com/trycua/cua
- **Stars:** 13,256
- **Description:** "Open-source infrastructure for Computer-Use Agents. Sandboxes, SDKs, and benchmarks to train and evaluate AI agents that can control full desktops."
- **Architecture:** Full VM environments (Apple Virtualization Framework on macOS, QEMU on Linux, Windows Sandbox). Provides complete desktop environments with display, mouse, keyboard.
- **Language/Runtime:** Python (SDK and agent framework), Swift (Lume VM manager)
- **Key Features:**
    - Full desktop VMs (macOS, Linux, Windows)
    - Agent framework for computer-use tasks
    - Benchmarking suite (OSWorld, ScreenSpot, Windows Arena)
    - CuaBot CLI for wrapping coding agents with desktop sandbox
    - Cloud and local deployment
- **Pros:**
    - Full desktop environment for computer-use agents
    - Multi-OS support
    - Benchmarking framework included
    - Large, active community
    - MIT license
- **Cons:**
    - Heavy -- full VM per agent
    - Slow startup (5-30s)
    - Primarily for computer-use, not code execution
    - macOS VMs require Apple hardware
- **License:** MIT
- **Activity:** Very active, rapidly growing

---

### 3.5 Kubernetes Agent Sandbox (kubernetes-sigs)

- **Repository:** https://github.com/kubernetes-sigs/agent-sandbox
- **Stars:** 1,480
- **Description:** "Agent-sandbox enables easy management of isolated, stateful, singleton workloads, ideal for use cases like AI agent runtimes."
- **Architecture:** Kubernetes CRD (Custom Resource Definition) that provides a `Sandbox` resource. Pluggable isolation backends -- supports gVisor and Kata Containers. Persistent volumes for state.
- **Language/Runtime:** Go (operator), Python SDK
- **Key Features:**
    - Kubernetes-native `Sandbox` CRD
    - Pluggable isolation backends (gVisor, Kata)
    - Persistent storage via PVC
    - Stateful singleton workloads
    - Python SDK (`k8s-agent-sandbox`)
    - Standardized API decoupled from isolation technology
- **Pros:**
    - Kubernetes-native -- fits existing K8s infrastructure
    - Pluggable backends for different security/performance tradeoffs
    - Backed by Kubernetes SIG Apps
    - Persistent state
    - Apache-2.0 license
- **Cons:**
    - Requires Kubernetes cluster
    - Heavier operational overhead than standalone solutions
    - Relatively new (experimental)
    - K8s-specific -- not usable outside Kubernetes
- **License:** Apache-2.0
- **Activity:** Active, official K8s SIG project

---

### 3.6 nono

- **Repository:** https://github.com/always-further/nono
- **Stars:** 1,237
- **Description:** "Kernel-enforced agent sandbox and agent security CLI and SDKs. Capability-based isolation with secure key management, atomic rollback, cryptographic immutable audit chain of provenance."
- **Architecture:** Uses kernel-level security mechanisms -- Landlock LSM on Linux (kernel 5.13+) and Seatbelt (sandbox_init) on macOS. No containers or VMs. Applies restrictions directly to the process. Default-deny capability model.
- **Language/Runtime:** Rust (CLI), Python SDK
- **Key Features:**
    - Kernel-enforced isolation (no container/VM overhead)
    - Filesystem ACLs (per-directory read/write/allow)
    - Network blocking
    - Secret management (macOS Keychain / Linux Secret Service)
    - Atomic rollback (snapshot/restore filesystem)
    - Cryptographic audit chain (Sigstore-based)
    - Zero startup overhead
- **Pros:**
    - Zero overhead -- no container or VM
    - Instant startup
    - Works on macOS and Linux
    - Strong secret management
    - Audit trail with cryptographic provenance
    - Apache-2.0 license
- **Cons:**
    - Process-level isolation only -- shared kernel, less isolation than microVM
    - Linux requires kernel 5.13+ for Landlock
    - Landlock has limited network filtering until ABI v4
    - Cannot isolate kernel-level exploits
    - Not suitable for fully untrusted code from adversarial sources
- **License:** Apache-2.0
- **Activity:** Active, growing

---

### 3.7 Gondolin

- **Repository:** https://github.com/earendil-works/gondolin
- **Stars:** 809
- **Description:** "Experimental Linux microvm setup with a TypeScript Control Plane as Agent Sandbox."
- **Architecture:** Firecracker microVMs managed by a TypeScript control plane. Programmable network and filesystem control. Designed for agents running generated code without human review.
- **Language/Runtime:** TypeScript (control plane)
- **Key Features:**
    - Firecracker microVM isolation
    - TypeScript control plane API
    - Programmable network policies
    - Filesystem control
- **Pros:**
    - Hardware-level isolation
    - TypeScript-native control plane
    - Programmable policies
    - Apache-2.0 license
- **Cons:**
    - Experimental
    - Small community
    - Limited documentation
    - Linux only (KVM required)
- **License:** Apache-2.0
- **Activity:** Active

---

### 3.8 Modal Sandboxes

- **Repository:** https://github.com/modal-labs/modal-client (SDK only; platform is proprietary)
- **Stars:** 451 (client SDK)
- **Description:** Modal is an AI infrastructure platform; Sandboxes is a product within it for running untrusted/agent-generated code with gVisor isolation.
- **Architecture:** gVisor (runsc) for kernel-level syscall interception. Sandbox environments defined at runtime via Python SDK. Part of a broader platform covering inference, training, and batch compute.
- **Language/Runtime:** Python (primary SDK), TypeScript and Go SDKs
- **Key Features:**
    - gVisor-based isolation
    - Define sandbox environments in one line of Python
    - Sub-second startup
    - GPU support for ML workloads
    - Tunneling for exposing services
    - 20k+ concurrent containers
    - $30/month free credits
    - Filesystem + memory persistence
- **Pros:**
    - GPU support (unique among sandboxes)
    - Integrated with broader compute platform
    - Sub-second startup
    - Flexible runtime image definition
    - Clean Python SDK
- **Cons:**
    - Cloud-only (no self-hosting)
    - gVisor provides weaker isolation than microVM
    - Proprietary platform
    - Vendor lock-in
- **License:** Apache-2.0 (SDK), Proprietary (platform)
- **Activity:** Very active

---

### 3.9 SWE-ReX

- **Repository:** https://github.com/SWE-agent/SWE-ReX
- **Stars:** 454
- **Description:** "Sandboxed code execution for AI agents, locally or on the cloud. Massively parallel, easy to extend. Powering SWE-agent and more."
- **Architecture:** Docker-based sandboxing with pluggable backends (local Docker, AWS Fargate, Modal). Designed specifically for software engineering agents. The agent sends commands; SWE-ReX executes them in isolation.
- **Language/Runtime:** Python
- **Key Features:**
    - Pluggable backends (Docker, Fargate, Modal)
    - Massively parallel execution
    - Powers SWE-agent (leading SE agent)
    - Easy to extend with custom backends
    - Local and cloud deployment
- **Pros:**
    - Purpose-built for SE agents
    - Flexible backend choice
    - Battle-tested with SWE-agent
    - MIT license
    - Easy to integrate
- **Cons:**
    - Container-level isolation only (unless using Modal backend)
    - Focused on SE tasks, less general
    - No native snapshot/restore
- **License:** MIT
- **Activity:** Active

---

### 3.10 Fly.io Sprites

- **Website:** https://sprites.dev
- **Description:** "A Sprite is a hardware-isolated execution environment for arbitrary code: a persistent Linux computer." Fly.io's purpose-built sandbox product for AI coding agents.
- **Architecture:** Firecracker microVMs on Fly.io's global infrastructure. Persistent -- filesystems survive between sessions. Dynamic resource allocation (VMs spin up only when needed).
- **Key Features:**
    - Firecracker microVM isolation
    - Persistent filesystem (packages, files survive)
    - Checkpointing and restore
    - Public URL exposure
    - Dynamic resource management (pay for actual usage)
    - Go, TypeScript, CLI SDKs
    - 100GB NVMe storage
- **Pros:**
    - Hardware-level isolation + persistence (unique combination)
    - Only billed for actual usage
    - Fast resume from checkpoint
    - Public URLs for exposed services
    - Global infrastructure
- **Cons:**
    - Cloud-only (Fly.io infrastructure)
    - No GPU support
    - Proprietary
    - Vendor lock-in to Fly.io
- **License:** Proprietary
- **Activity:** Active, launched January 2026

---

### 3.11 Docker Sandboxes

- **Website:** https://www.docker.com/blog/docker-sandboxes-a-new-approach-for-coding-agent-safety/
- **Description:** Experimental Docker Desktop feature for running AI coding agents in isolated environments. Transitioning from container-based to microVM-based isolation.
- **Architecture:** Currently container-based isolation inside Docker Desktop's VM, migrating to dedicated microVMs. Bind-mounted workspace directory. Network proxy with policy controls.
- **Key Features:**
    - `docker sandbox run <agent>` CLI
    - Workspace mirroring (bind mounts)
    - Network policy control (`docker sandbox network proxy`)
    - Docker-in-Docker support
    - CLAUDE.md configuration
    - NanoClaw integration for agent frameworks
- **Pros:**
    - Familiar Docker ecosystem
    - Easy to use for existing Docker users
    - Local-first
    - Network policy controls
    - No cloud dependency
- **Cons:**
    - Experimental / early stage
    - Currently container-level isolation (microVM migration planned)
    - Requires Docker Desktop
    - Proprietary (Docker Desktop license)
    - Limited to local execution
- **License:** Proprietary (Docker Desktop)
- **Activity:** Experimental, actively developed

---

### 3.12 Together Code Sandbox

- **Website:** https://www.together.ai/sandbox
- **Description:** Together AI's code sandbox product built on CodeSandbox SDK infrastructure.
- **Architecture:** Full VM with memory snapshots. Built on CodeSandbox SDK infrastructure.
- **Key Features:**
    - VM isolation
    - Memory + filesystem snapshots
    - 500ms resume from snapshot (2.7s cold start)
    - VM cloning in 3 seconds
    - Up to 64 vCPU, 128 GB RAM per sandbox
    - GPU support via Together's inference platform
    - CodeSandbox SDK API
- **Pros:**
    - High resource limits (64 vCPU, 128 GB RAM)
    - Memory snapshots (not just filesystem)
    - Integrated with Together AI's inference platform
    - GPU access
- **Cons:**
    - Cloud-only
    - Proprietary
    - Young ecosystem
    - Pricing tied to Together AI
- **License:** Proprietary
- **Activity:** Active

---

### 3.13 Blaxel

- **Website:** https://blaxel.ai
- **Description:** Managed AI agent infrastructure platform with persistent microVM sandboxes and ultra-fast resume times.
- **Architecture:** microVM isolation with root filesystem in memory. Perpetual persistence (sandboxes survive indefinitely). ~25ms resume time.
- **Key Features:**
    - 25ms resume time
    - Perpetual sandbox persistence
    - microVM isolation
    - Python and TypeScript SDKs
    - Scale-to-zero with instant resume
    - Serverless agent hosting
- **Pros:**
    - Fastest resume time in the market (25ms)
    - Perpetual persistence
    - Scale-to-zero billing
- **Cons:**
    - Cloud-only
    - Proprietary
    - Smaller community
- **License:** Proprietary
- **Activity:** Active

---

### 3.14 CodeSandbox SDK

- **Repository:** https://github.com/codesandbox/codesandbox-sdk
- **Stars:** 102
- **Description:** "Programmatically start (AI) sandboxes on top of CodeSandbox." The infrastructure that powers Together Code Sandbox.
- **Architecture:** Firecracker microVM isolation. Snapshot and clone support.
- **Language/Runtime:** TypeScript
- **Key Features:**
    - Programmatic sandbox creation
    - Snapshot and restore
    - VM cloning
    - File system and process APIs
    - Preview URLs
- **Pros:**
    - Powers major platforms (Together AI)
    - TypeScript-first
    - Snapshot/clone support
- **Cons:**
    - Cloud-only
    - Proprietary platform (SDK is source-available)
    - Primarily TypeScript
- **License:** Proprietary (source-available SDK)
- **Activity:** Active

---

### 3.15 Cloudflare Sandbox SDK

- **Website:** https://developers.cloudflare.com/sandbox/
- **Description:** Sandbox SDK for running untrusted code in isolated environments on Cloudflare's edge infrastructure.
- **Architecture:** Built on Cloudflare Containers (container-based isolation). Runs on Cloudflare's global edge network.
- **Key Features:**
    - Edge deployment (global, low latency)
    - TypeScript SDK
    - File system, process, and service APIs
    - Preview URLs
    - Integrated with Workers ecosystem
    - Pay-per-use pricing
    - Python and Node.js runtime support
- **Pros:**
    - Global edge network (low latency everywhere)
    - Instant startup
    - No infrastructure to manage
    - Integrated with Cloudflare ecosystem
- **Cons:**
    - Container-level isolation (not microVM)
    - Cloud-only (Cloudflare infrastructure)
    - Proprietary
    - Limited to Cloudflare Workers context
- **License:** Proprietary
- **Activity:** Active

---

### 3.16 Northflank Sandboxes

- **Website:** https://northflank.com
- **Description:** Production-grade sandbox infrastructure with microVM isolation, supporting BYOC (bring your own cloud) deployment.
- **Architecture:** Supports multiple isolation backends: Kata Containers, Firecracker, gVisor. Deploys to managed cloud or customer's own AWS/GCP/Azure/bare-metal.
- **Key Features:**
    - Multiple isolation backends (Kata, Firecracker, gVisor)
    - BYOC deployment
    - Ephemeral and persistent environments
    - Full infrastructure platform (databases, APIs, CI/CD, GPUs)
    - SSH access
    - Pause/resume
    - Snapshots
- **Pros:**
    - Flexible isolation technology choice
    - BYOC for compliance requirements
    - Full platform (not just sandboxes)
    - Multi-cloud support
- **Cons:**
    - Proprietary
    - Complex platform -- may be overkill for just sandboxing
    - Pricing unclear
- **License:** Proprietary
- **Activity:** Active

---

### 3.17 Runloop

- **Website:** https://runloop.ai
- **Description:** Enterprise-grade infrastructure platform for AI coding agents. Devboxes provide isolated, cloud-hosted development environments.
- **Architecture:** microVM isolation with hardware-level boundaries. SOC2-compliant.
- **Key Features:**
    - Devbox sandbox environments
    - Blueprints (environment templates)
    - Snapshots and suspend/resume
    - Code Mounts and Repo Connect
    - Custom benchmarking
    - MCP Hub integration
    - Docker-in-Docker
    - Browser and Desktop (Ubuntu) environments
    - Agent Gateways
    - Python and TypeScript SDKs
- **Pros:**
    - Enterprise-grade (SOC2)
    - Rich feature set
    - MCP integration
    - Benchmarking tools
- **Cons:**
    - Cloud-only
    - Proprietary
    - Enterprise pricing
- **License:** Proprietary
- **Activity:** Active

---

### 3.18 EdgeBox

- **Repository:** https://github.com/BIGPPWONG/EdgeBox
- **Stars:** 199
- **Description:** "A fully-featured, GUI-powered local LLM Agent sandbox with complete MCP protocol support." Fork of E2B open-source code, designed for local use.
- **Architecture:** Firecracker microVM (based on E2B open-source infrastructure). Includes CLI and full desktop environment.
- **Key Features:**
    - Local deployment
    - MCP protocol support
    - GUI desktop environment
    - Browser, terminal, desktop application support
    - Based on E2B open-source code
- **Pros:**
    - Local-first
    - Full desktop environment
    - MCP support
- **Cons:**
    - GPL-3.0 license (strong copyleft)
    - Based on E2B -- derivative work
    - Smaller community
- **License:** GPL-3.0
- **Activity:** Active

---

### 3.19 OpenKruise Agents

- **Repository:** https://github.com/openkruise/agents
- **Stars:** 130
- **Description:** "Rapid and cost-effective operator and best practice for agent sandbox lifecycle management." Kubernetes operator for agent sandbox lifecycle.
- **Architecture:** Kubernetes operator managing pod-based sandboxes with lifecycle automation.
- **License:** Apache-2.0
- **Activity:** Active

---

### 3.20 Other Notable Projects

| Project | Stars | Description |
|---|---|---|
| **ms-enclave** (ModelScope) | 46 | Modular agent sandbox runtime from Alibaba's ModelScope |
| **shipyard** (AstrBotDevs) | 43 | Lightweight agent sandbox with Python interpreter, shell, filesystem |
| **the-agent-sandbox-taxonomy** | 41 | Taxonomy and scoring framework for evaluating 26 sandboxes |
| **agentbox** | 37 | "A computer for your agent" -- sandboxed code execution |
| **kira** | 32 | Fast, scalable general-purpose sandbox code execution engine in Go |
| **nix-sandbox-mcp** | 13 | Sandboxed code execution for LLMs powered by Nix |

---

## 4. Isolation Technology Deep Dive

### 4.1 Firecracker microVMs
**Used by:** E2B, BoxLite, Fly.io Sprites, Gondolin, CodeSandbox SDK, EdgeBox

Firecracker (33k+ stars, by AWS) is a lightweight VMM that creates microVMs in ~125ms. Each VM gets its own kernel, providing hardware-level isolation. This is the strongest widely-available isolation for agent sandboxes.

**Tradeoffs:**
- (+) Hardware-level isolation -- kernel exploits in the guest cannot affect the host
- (+) Fast startup (~125ms for the VMM, ~1-2s for full environment)
- (+) Minimal resource overhead (~5MB per VM)
- (-) Requires Linux with KVM support
- (-) No GPU passthrough (CPU-only workloads)
- (-) More complex to manage than containers

### 4.2 gVisor (runsc)
**Used by:** Modal, Kubernetes Agent Sandbox (optional), Northflank (optional)

gVisor (18k stars, by Google) is an application kernel that intercepts syscalls in userspace. Containers run with gVisor as the runtime instead of the default runc.

**Tradeoffs:**
- (+) Stronger isolation than plain containers
- (+) No KVM requirement
- (+) Compatible with OCI container ecosystem
- (-) Weaker isolation than microVM (shared host kernel, just syscall filtering)
- (-) Some syscall compatibility issues
- (-) Performance overhead for syscall-heavy workloads

### 4.3 Kata Containers
**Used by:** Kubernetes Agent Sandbox (optional), Northflank (optional)

Kata Containers run each container inside a lightweight VM. Combines OCI compatibility with hardware-level isolation.

**Tradeoffs:**
- (+) Hardware-level isolation with container API
- (+) OCI-compatible
- (-) Higher overhead than Firecracker alone
- (-) More complex operational model

### 4.4 Kernel Security Modules (Landlock, Seatbelt)
**Used by:** nono

Process-level sandboxing using kernel security features. No containers or VMs.

**Tradeoffs:**
- (+) Zero overhead
- (+) Instant startup
- (+) Cross-platform (Linux + macOS)
- (-) Process-level only -- shared kernel with host
- (-) Cannot prevent kernel exploits
- (-) Limited network control (Landlock ABI v4 needed)

### 4.5 Plain Docker Containers
**Used by:** Daytona, SWE-ReX, Docker Sandboxes (current)

Standard OCI containers with namespace and cgroup isolation.

**Tradeoffs:**
- (+) Ubiquitous, well-understood
- (+) Fast startup
- (+) Rich ecosystem
- (-) Shared kernel -- container escapes are a real risk for untrusted code
- (-) Not sufficient isolation for adversarial inputs

---

## 5. Recommendations for toolregistry-hub Integration

### 5.1 Use Case Analysis

toolregistry-hub provides pre-configured tool registries served via MCP/OpenAPI. A sandbox integration would enable:

1. **Safe tool execution:** Tools that execute code (shell commands, scripts, data processing) run in isolation
2. **Multi-tenant isolation:** Different users' tool executions are isolated from each other
3. **Ephemeral environments:** Spin up a sandbox, execute tool code, return results, tear down
4. **Persistent environments:** Long-running tool sessions with state

### 5.2 Recommended Approach: Layered Integration

Rather than locking into a single sandbox provider, toolregistry-hub should define an **abstract sandbox interface** and support multiple backends:

```
ToolRegistry
  └── SandboxExecutor (abstract)
        ├── DockerSandbox (self-hosted, simple)
        ├── E2BSandbox (cloud, strong isolation)
        ├── BoxLiteSandbox (embedded, local)
        ├── DaytonaSandbox (cloud/self-hosted, fast)
        └── ModalSandbox (cloud, GPU support)
```

### 5.3 Tier 1 Recommendations (Prioritize)

| Solution | Why | Best For |
|---|---|---|
| **E2B** | Industry standard, clean SDK, Apache-2.0, strong isolation | Cloud deployment, untrusted code |
| **BoxLite** | Embeddable, no daemon, local-first, Apache-2.0 | Self-hosted / local deployment |
| **Docker (plain)** | Simplest, no extra dependencies | Development, trusted code |

### 5.4 Tier 2 Recommendations (Consider)

| Solution | Why | Best For |
|---|---|---|
| **Daytona** | Largest community, fast, but AGPL license is restrictive | Teams OK with AGPL |
| **Modal** | GPU support, good SDK | ML/GPU workloads |
| **nono** | Zero-overhead for process-level sandboxing | Quick local isolation |
| **SWE-ReX** | Pluggable backends, MIT license, Python-native | SE agent use cases |

### 5.5 Implementation Strategy

1. **Define a `SandboxBackend` protocol** in toolregistry-hub with methods like `create()`, `execute()`, `destroy()`, `snapshot()`, `restore()`
2. **Start with Docker** as the default backend (lowest barrier)
3. **Add E2B** as the recommended cloud backend for production
4. **Add BoxLite** as the recommended embedded backend for local/self-hosted
5. **Keep the interface generic** so additional backends (Modal, Daytona, Sprites, etc.) can be added by the community

### 5.6 Key Design Considerations

- **Timeout and resource limits:** All sandbox backends must enforce CPU time, memory, and wall-clock limits
- **Network control:** Ability to deny/allow specific network access per sandbox
- **Filesystem isolation:** Tool code should not access host filesystem
- **Secret injection:** Secure mechanism for passing API keys into sandboxes
- **Cleanup:** Guaranteed sandbox destruction after execution (no leaked VMs/containers)
- **Observability:** Logging of all commands executed within sandboxes
- **Cost model:** Cloud backends have per-second billing; design for short-lived sandboxes

---

## 6. References

### Repositories
- Daytona: https://github.com/daytonaio/daytona
- E2B: https://github.com/e2b-dev/E2B
- E2B Infra: https://github.com/e2b-dev/infra
- BoxLite: https://github.com/boxlite-ai/boxlite
- CUA: https://github.com/trycua/cua
- K8s Agent Sandbox: https://github.com/kubernetes-sigs/agent-sandbox
- nono: https://github.com/always-further/nono
- Gondolin: https://github.com/earendil-works/gondolin
- Modal Client: https://github.com/modal-labs/modal-client
- SWE-ReX: https://github.com/SWE-agent/SWE-ReX
- EdgeBox: https://github.com/BIGPPWONG/EdgeBox
- CodeSandbox SDK: https://github.com/codesandbox/codesandbox-sdk
- OpenKruise Agents: https://github.com/openkruise/agents
- Firecracker: https://github.com/firecracker-microvm/firecracker
- gVisor: https://github.com/google/gvisor
- Agent Sandbox Taxonomy: https://github.com/kajogo777/the-agent-sandbox-taxonomy

### Articles and Comparisons
- Sandbox Showdown: E2B vs Daytona -- https://www.zenml.io/blog/e2b-vs-daytona
- E2B vs Modal -- https://northflank.com/blog/e2b-vs-modal
- How to Sandbox AI Agents in 2026 -- https://northflank.com/blog/how-to-sandbox-ai-agents
- AI Code Sandbox Benchmark 2026 -- https://www.superagent.sh/blog/ai-code-sandbox-benchmark-2026
- AI Agent Sandboxes Compared -- https://rywalker.com/research/ai-agent-sandboxes
- Top AI Code Sandbox Products -- https://modal.com/blog/top-code-agent-sandbox-products
- Let's Talk About Sandboxes (BoxLite) -- https://medium.com/@yingjunwu/lets-talk-about-sandboxes-f055f2b4b003
- Two Ways to Sandbox Agents (Browser Use) -- https://browser-use.com/posts/two-ways-to-sandbox-agents
- Running Agents on Kubernetes with Agent Sandbox -- https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/

### Product Pages
- Fly.io Sprites: https://sprites.dev
- Blaxel: https://blaxel.ai/vm
- Runloop: https://runloop.ai
- Together Code Sandbox: https://www.together.ai/sandbox
- Cloudflare Sandbox SDK: https://developers.cloudflare.com/sandbox/
- Docker Sandboxes: https://www.docker.com/blog/docker-sandboxes-a-new-approach-for-coding-agent-safety/
- Northflank Sandboxes: https://northflank.com
