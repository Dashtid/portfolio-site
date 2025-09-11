async function globalSetup(config) {
  console.log('Setting up tests...')
  
  // Any global setup logic here
  // For example: start services, create test data, etc.
  
  return async () => {
    console.log('Global teardown...')
    // Cleanup logic
  }
}

export default globalSetup