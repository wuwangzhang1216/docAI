/**
 * PWA Icon Generator Script
 *
 * This script generates PNG icons of various sizes from the SVG source.
 *
 * Usage:
 *   node scripts/generate-icons.js
 *
 * Requirements:
 *   npm install sharp
 */

const fs = require('fs');
const path = require('path');

// Check if sharp is available
let sharp;
try {
  sharp = require('sharp');
} catch (e) {
  console.log('Sharp not installed. Installing...');
  const { execSync } = require('child_process');
  execSync('npm install sharp', { stdio: 'inherit' });
  sharp = require('sharp');
}

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const inputSvg = path.join(__dirname, '../public/icons/icon.svg');
const outputDir = path.join(__dirname, '../public/icons');

async function generateIcons() {
  console.log('Generating PWA icons...\n');

  // Ensure output directory exists
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Read SVG file
  const svgBuffer = fs.readFileSync(inputSvg);

  for (const size of sizes) {
    const outputPath = path.join(outputDir, `icon-${size}x${size}.png`);

    try {
      await sharp(svgBuffer)
        .resize(size, size)
        .png()
        .toFile(outputPath);

      console.log(`✓ Generated: icon-${size}x${size}.png`);
    } catch (error) {
      console.error(`✗ Failed to generate icon-${size}x${size}.png:`, error.message);
    }
  }

  // Generate favicon.ico (16x16, 32x32, 48x48)
  try {
    await sharp(svgBuffer)
      .resize(32, 32)
      .png()
      .toFile(path.join(outputDir, '../favicon.png'));
    console.log(`✓ Generated: favicon.png`);
  } catch (error) {
    console.error(`✗ Failed to generate favicon.png:`, error.message);
  }

  // Generate Apple touch icon (180x180)
  try {
    await sharp(svgBuffer)
      .resize(180, 180)
      .png()
      .toFile(path.join(outputDir, 'apple-touch-icon.png'));
    console.log(`✓ Generated: apple-touch-icon.png`);
  } catch (error) {
    console.error(`✗ Failed to generate apple-touch-icon.png:`, error.message);
  }

  console.log('\nDone! All icons generated successfully.');
}

generateIcons().catch(console.error);
