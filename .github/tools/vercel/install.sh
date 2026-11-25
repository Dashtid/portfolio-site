#!/usr/bin/env bash
# Install the Vercel CLI from this folder's lock into $RUNNER_TEMP/vercel-cli,
# outside the checkout that `vercel deploy` uploads, and fail unless the binary
# runs and prints the locked version. ci-cd.yml runs this in deploy-frontend
# and, with no secrets, in vercel-cli on pull requests; rebake-frontend.yml
# runs it before its deploy.
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
target="${RUNNER_TEMP}/vercel-cli"
mkdir -p "${target}"
cp "${here}/package.json" "${here}/package-lock.json" "${target}/"
cd "${target}"
npm ci --ignore-scripts --no-audit --no-fund
cli=node_modules/@vercel/vc-native-linux-x64
test -x "${cli}/bin/vercel"
want=$(node -p "require('./${cli}/package.json').version")
# The version goes to stdout and the banner to stderr.
"${cli}/bin/vercel" --version | tee version.txt
grep -qxF "${want}" version.txt
