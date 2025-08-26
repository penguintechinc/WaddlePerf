#!/bin/bash

# Build script for Cloudflare Pages
cd website
npm ci
npm run build