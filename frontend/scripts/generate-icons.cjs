#!/usr/bin/env node
/**
 * PWA Icon Generator for AI Manus
 * Generates all required icon sizes for PWA and app stores
 */
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const maskableSizes = [192, 512];
const iconsDir = path.join(__dirname, '../public/icons');

// AI Manus brand colors
const brandColor = '#6366f1'; // Indigo

// Create a simple SVG icon with "M" for Manus
function createIconSVG(size, isMaskable = false) {
  const padding = isMaskable ? size * 0.1 : 0;
  const fontSize = (size - padding * 2) * 0.5;
  const centerX = size / 2;
  const centerY = size / 2;

  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
  <rect width="${size}" height="${size}" fill="${brandColor}" rx="${isMaskable ? 0 : size * 0.15}"/>
  <text x="${centerX}" y="${centerY + fontSize * 0.35}"
        font-family="Arial, Helvetica, sans-serif"
        font-size="${fontSize}"
        font-weight="bold"
        fill="white"
        text-anchor="middle">M</text>
</svg>`);
}

async function generateIcons() {
  // Ensure directory exists
  if (!fs.existsSync(iconsDir)) {
    fs.mkdirSync(iconsDir, { recursive: true });
  }

  console.log('Generating PWA icons...');

  // Generate regular icons
  for (const size of sizes) {
    const svg = createIconSVG(size, false);
    const filename = `icon-${size}x${size}.png`;
    await sharp(svg).png().toFile(path.join(iconsDir, filename));
    console.log(`  ✓ ${filename}`);
  }

  // Generate maskable icons
  for (const size of maskableSizes) {
    const svg = createIconSVG(size, true);
    const filename = `icon-maskable-${size}x${size}.png`;
    await sharp(svg).png().toFile(path.join(iconsDir, filename));
    console.log(`  ✓ ${filename}`);
  }

  // Generate Apple touch icon (180x180)
  const appleSvg = createIconSVG(180, false);
  await sharp(appleSvg).png().toFile(path.join(iconsDir, 'apple-touch-icon.png'));
  console.log('  ✓ apple-touch-icon.png');

  // Generate favicon (32x32)
  const faviconSvg = createIconSVG(32, false);
  await sharp(faviconSvg).png().toFile(path.join(iconsDir, 'favicon-32x32.png'));
  console.log('  ✓ favicon-32x32.png');

  console.log('\\nAll icons generated successfully!');
}

generateIcons().catch(console.error);
