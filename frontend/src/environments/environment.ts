/**
 * Environment configuration for development.
 */
export const ENVIRONMENT = {
  production: false,
  // Envoy proxy URL for gRPC-Web communication
  // Envoy runs on port 8080 and proxies to the gRPC backend on port 50051
  grpcWebUrl: 'http://localhost:8080',
};
