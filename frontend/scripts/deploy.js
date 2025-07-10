#!/usr/bin/env node

// Deployment Script for ChatBot SAAS Frontend
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ENVIRONMENTS = {
  development: {
    envFile: '.env',
    buildCommand: 'npm run build',
    outputDir: 'dist',
  },
  staging: {
    envFile: '.env.staging',
    buildCommand: 'npm run build',
    outputDir: 'dist',
  },
  production: {
    envFile: '.env.production',
    buildCommand: 'npm run build',
    outputDir: 'dist',
  },
};

function log(message, type = 'info') {
  const colors = {
    info: '\x1b[36m',
    success: '\x1b[32m',
    warning: '\x1b[33m',
    error: '\x1b[31m',
    reset: '\x1b[0m',
  };
  
  console.log(`${colors[type]}[${type.toUpperCase()}]${colors.reset} ${message}`);
}

function validateEnvironment(env) {
  if (!ENVIRONMENTS[env]) {
    log(`Invalid environment: ${env}. Available: ${Object.keys(ENVIRONMENTS).join(', ')}`, 'error');
    process.exit(1);
  }
}

function checkPrerequisites() {
  log('Checking prerequisites...');
  
  // Check if package.json exists
  if (!fs.existsSync('package.json')) {
    log('package.json not found. Make sure you\'re in the project root.', 'error');
    process.exit(1);
  }
  
  // Check if node_modules exists
  if (!fs.existsSync('node_modules')) {
    log('node_modules not found. Running npm install...', 'warning');
    execSync('npm install', { stdio: 'inherit' });
  }
  
  log('Prerequisites check passed', 'success');
}

function validateEnvFile(envFile) {
  log(`Validating environment file: ${envFile}`);
  
  if (!fs.existsSync(envFile)) {
    log(`Environment file ${envFile} not found`, 'error');
    process.exit(1);
  }
  
  const envContent = fs.readFileSync(envFile, 'utf8');
  const requiredVars = [
    'PUBLIC_API_URL',
    'PUBLIC_APP_URL',
  ];
  
  const missingVars = requiredVars.filter(varName => 
    !envContent.includes(`${varName}=`) || 
    envContent.includes(`${varName}=`) && envContent.split(`${varName}=`)[1].split('\n')[0].trim() === ''
  );
  
  if (missingVars.length > 0) {
    log(`Missing required environment variables: ${missingVars.join(', ')}`, 'error');
    process.exit(1);
  }
  
  log('Environment file validation passed', 'success');
}

function runSecurityChecks() {
  log('Running security checks...');
  
  try {
    // Check for npm audit issues
    execSync('npm audit --audit-level=high', { stdio: 'pipe' });
    log('No high-severity security vulnerabilities found', 'success');
  } catch (error) {
    log('Security vulnerabilities detected. Run "npm audit fix" to resolve.', 'warning');
    
    // Don't fail deployment for audit issues in development
    const env = process.argv[2] || 'development';
    if (env === 'production') {
      log('Deployment blocked due to security issues in production', 'error');
      process.exit(1);
    }
  }
}

function runTests() {
  log('Running tests...');
  
  try {
    // Check if test script exists
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    if (packageJson.scripts && packageJson.scripts.test) {
      execSync('npm test', { stdio: 'inherit' });
      log('All tests passed', 'success');
    } else {
      log('No test script found, skipping tests', 'warning');
    }
  } catch (error) {
    log('Tests failed', 'error');
    process.exit(1);
  }
}

function buildProject(config) {
  log(`Building project for ${process.argv[2]} environment...`);
  
  try {
    // Copy environment file
    if (fs.existsSync(config.envFile)) {
      fs.copyFileSync(config.envFile, '.env');
      log(`Using environment file: ${config.envFile}`, 'info');
    }
    
    // Run build command
    execSync(config.buildCommand, { stdio: 'inherit' });
    
    // Verify build output
    if (!fs.existsSync(config.outputDir)) {
      throw new Error(`Build output directory ${config.outputDir} not found`);
    }
    
    log('Build completed successfully', 'success');
  } catch (error) {
    log(`Build failed: ${error.message}`, 'error');
    process.exit(1);
  }
}

function generateBuildInfo(env) {
  log('Generating build information...');
  
  const buildInfo = {
    environment: env,
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
    commit: process.env.GITHUB_SHA || 'unknown',
    branch: process.env.GITHUB_REF_NAME || 'unknown',
    buildNumber: process.env.GITHUB_RUN_NUMBER || 'local',
  };
  
  try {
    // Try to get git info if available
    try {
      buildInfo.commit = execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
      buildInfo.branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
    } catch (gitError) {
      log('Git information not available', 'warning');
    }
    
    fs.writeFileSync('dist/build-info.json', JSON.stringify(buildInfo, null, 2));
    log('Build information generated', 'success');
  } catch (error) {
    log(`Failed to generate build info: ${error.message}`, 'warning');
  }
}

function optimizeBuild() {
  log('Optimizing build...');
  
  try {
    // Remove source maps in production
    const env = process.argv[2] || 'development';
    if (env === 'production') {
      const distPath = 'dist';
      const files = fs.readdirSync(distPath, { recursive: true });
      
      files.forEach(file => {
        if (file.endsWith('.map')) {
          const filePath = path.join(distPath, file);
          if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
            log(`Removed source map: ${file}`, 'info');
          }
        }
      });
    }
    
    log('Build optimization completed', 'success');
  } catch (error) {
    log(`Build optimization failed: ${error.message}`, 'warning');
  }
}

function showDeploymentInstructions(env) {
  log('\n=== Deployment Instructions ===', 'info');
  
  const instructions = {
    development: [
      'Your development build is ready!',
      'To serve locally: npm run preview',
      'Build output is in: ./dist',
    ],
    staging: [
      'Your staging build is ready!',
      'Upload the ./dist folder to your staging server',
      'Configure your web server to serve static files',
      'Set up proper redirects for SPA routing',
    ],
    production: [
      'Your production build is ready!',
      'IMPORTANT: Review the following before deploying:',
      '1. Verify all environment variables are set correctly',
      '2. Ensure HTTPS is configured',
      '3. Set up proper security headers',
      '4. Configure CDN if applicable',
      '5. Set up monitoring and error tracking',
      '',
      'Upload the ./dist folder to your production server',
    ],
  };
  
  instructions[env].forEach(instruction => {
    log(instruction, 'info');
  });
  
  log('\n=== Build Summary ===', 'success');
  log(`Environment: ${env}`, 'info');
  log(`Build directory: ./dist`, 'info');
  log(`Build completed at: ${new Date().toLocaleString()}`, 'info');
}

// Main deployment function
function deploy() {
  const env = process.argv[2] || 'development';
  
  log(`Starting deployment for ${env} environment...`, 'info');
  
  validateEnvironment(env);
  checkPrerequisites();
  
  const config = ENVIRONMENTS[env];
  validateEnvFile(config.envFile);
  
  if (env === 'production') {
    runSecurityChecks();
    runTests();
  }
  
  buildProject(config);
  generateBuildInfo(env);
  optimizeBuild();
  
  log(`Deployment for ${env} completed successfully!`, 'success');
  showDeploymentInstructions(env);
}

// Handle command line arguments
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
Usage: node scripts/deploy.js [environment]

Environments:
  development  - Build for development (default)
  staging      - Build for staging
  production   - Build for production

Options:
  --help, -h   - Show this help message

Examples:
  node scripts/deploy.js development
  node scripts/deploy.js production
  npm run deploy:prod
    `);
    process.exit(0);
  }
  
  deploy();
}

module.exports = { deploy };
