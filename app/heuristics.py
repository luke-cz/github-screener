from __future__ import annotations

from dataclasses import dataclass, field


TEST_HINTS = {
    "tests",
    "test",
    "__tests__",
    "pytest.ini",
    "jest.config.js",
    "jest.config.ts",
    "go.test",
}

CI_HINTS = {
    ".github",
    ".gitlab-ci.yml",
    "azure-pipelines.yml",
    ".circleci",
}

LINT_HINTS = {
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.json",
    ".eslintrc.yml",
    ".flake8",
    "ruff.toml",
    "pylintrc",
    ".golangci.yml",
    ".golangci.yaml",
    ".rustfmt.toml",
}

DOCS_HINTS = {"readme.md", "docs", "contributing.md", "changelog.md"}

SECURITY_HINTS = {"security.md", "dependabot.yml", ".github/dependabot.yml"}

INFRA_HINTS = {
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "kubernetes",
    "k8s",
    "helm",
    "terraform",
    "main.tf",
    "cdk.json",
    "pulumi.yaml",
    "cloudformation",
}

SOLIDITY_HINTS = {
    "hardhat.config.js",
    "hardhat.config.ts",
    "foundry.toml",
    "truffle-config.js",
    "slither.config.json",
}

RUST_SC_HINTS = {
    "anchor.toml",
    "cargo.toml",
    "cosmwasm",
    "ink",
}

FRONTEND_HINTS = {
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
    "vite.config.js",
    "vite.config.ts",
    "webpack.config.js",
    "webpack.config.ts",
    "react",
}

MOBILE_HINTS = {
    "android",
    "ios",
    "pubspec.yaml",
}


@dataclass
class RepoSignals:
    tests: bool = False
    ci: bool = False
    lint: bool = False
    docs: bool = False
    security: bool = False
    infra: bool = False
    solidity: bool = False
    rust_sc: bool = False
    frontend: bool = False
    mobile: bool = False
    evidence: list[str] = field(default_factory=list)


def _normalize(items: list[str]) -> set[str]:
    return {item.lower() for item in items}


def detect_signals(file_names: list[str]) -> RepoSignals:
    normalized = _normalize(file_names)
    signals = RepoSignals()

    def mark(condition: bool, label: str) -> None:
        if condition:
            signals.evidence.append(label)

    if normalized & TEST_HINTS:
        signals.tests = True
        mark(True, "tests")
    if normalized & CI_HINTS or ".github/workflows" in normalized:
        signals.ci = True
        mark(True, "ci")
    if normalized & LINT_HINTS:
        signals.lint = True
        mark(True, "lint")
    if normalized & DOCS_HINTS:
        signals.docs = True
        mark(True, "docs")
    if normalized & SECURITY_HINTS:
        signals.security = True
        mark(True, "security")
    if normalized & INFRA_HINTS:
        signals.infra = True
        mark(True, "infra")
    if normalized & SOLIDITY_HINTS:
        signals.solidity = True
        mark(True, "solidity")
    if normalized & RUST_SC_HINTS:
        signals.rust_sc = True
        mark(True, "rust_smart_contracts")
    if normalized & FRONTEND_HINTS:
        signals.frontend = True
        mark(True, "frontend")
    if normalized & MOBILE_HINTS:
        signals.mobile = True
        mark(True, "mobile")

    return signals
