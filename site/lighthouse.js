// Scores the built site with Lighthouse and fails under the floor.
//
// Lighthouse is fetched by npx at a pinned version and kept out of package.json on
// purpose: its dependency tree carried 27 open advisories on 2026-10-13, which would fail
// `npm audit` for a tool that never touches the shipped site.
// ponytail: pinned by version, not by a lock-file hash. Acceptable because the CI job that
// runs this holds no secrets and builds nothing that deploys. Upgrade path: its own
// package.json and lock file in a tools/ folder.
import { spawn } from "node:child_process";
import { mkdirSync, readFileSync } from "node:fs";
import { preview } from "vite";

const LIGHTHOUSE_VERSION = "12.8.2";
// Every category must reach 95, on Lighthouse's default mobile profile.
const FLOOR = 0.95;
const PORT = 4173;
const REPORT = ".lighthouse/report.json";

// Lighthouse must run as an async child. A synchronous call would block this process, and
// this process is also the server Lighthouse is loading the page from.
function run(command, args) {
  return new Promise((resolve, reject) => {
    // npx is npx.cmd on Windows, which only a shell can run.
    const child = spawn(command, args, { stdio: "inherit", shell: true });
    child.on("error", reject);
    child.on("exit", (code) =>
      code === 0
        ? resolve()
        : reject(new Error(`${command} exited with ${code}`)),
    );
  });
}

const server = await preview({ preview: { port: PORT, strictPort: true } });
let failed = false;
try {
  mkdirSync(".lighthouse", { recursive: true });
  await run("npx", [
    "--yes",
    `lighthouse@${LIGHTHOUSE_VERSION}`,
    `http://localhost:${PORT}/`,
    "--output=json",
    `--output-path=${REPORT}`,
    "--chrome-flags=--headless=new",
    "--quiet",
  ]);
  const { categories } = JSON.parse(readFileSync(REPORT, "utf8"));
  for (const { title, score } of Object.values(categories)) {
    const ok = score >= FLOOR;
    console.log(
      `${ok ? "pass" : "FAIL"}  ${Math.round(score * 100)}  ${title}`,
    );
    failed ||= !ok;
  }
} finally {
  await server.close();
}
process.exit(failed ? 1 : 0);
